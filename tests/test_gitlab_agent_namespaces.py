"""Render with Helm against a local fake Kubernetes API; no real cluster access."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

import yaml


CHART = Path(__file__).resolve().parents[1] / "charts/gitlab-agent-rbac"


class NamespaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.existing = {}
        self.denied = set()
        test = self

        class API(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                path = urlsplit(self.path).path
                code = 200
                if path == "/version":
                    body = {"major": "1", "minor": "36", "gitVersion": "v1.36.4"}
                elif path == "/api":
                    body = {"kind": "APIVersions", "versions": ["v1"]}
                elif path == "/apis":
                    body = {"kind": "APIGroupList", "groups": [{
                        "name": "rbac.authorization.k8s.io",
                        "versions": [{"groupVersion": "rbac.authorization.k8s.io/v1", "version": "v1"}],
                        "preferredVersion": {"groupVersion": "rbac.authorization.k8s.io/v1", "version": "v1"}}]}
                elif path in ("/api/v1", "/apis/rbac.authorization.k8s.io/v1"):
                    core = path == "/api/v1"
                    resources = [("namespaces", "Namespace", False), ("serviceaccounts", "ServiceAccount", True)] if core else [
                        ("roles", "Role", True), ("rolebindings", "RoleBinding", True),
                        ("clusterroles", "ClusterRole", False), ("clusterrolebindings", "ClusterRoleBinding", False)]
                    body = {"kind": "APIResourceList", "groupVersion": "v1" if core else "rbac.authorization.k8s.io/v1",
                            "resources": [{"name": name, "kind": kind, "namespaced": namespaced,
                                           "verbs": ["get", "list"]} for name, kind, namespaced in resources]}
                elif path.startswith("/api/v1/namespaces/") and path.rsplit("/", 1)[1] in test.denied:
                    code, body = 403, {"kind": "Status", "apiVersion": "v1", "status": "Failure", "reason": "Forbidden", "message": "Forbidden namespace lookup", "code": 403}
                elif path.startswith("/api/v1/namespaces/") and path.rsplit("/", 1)[1] in test.existing:
                    body = test.existing[path.rsplit("/", 1)[1]]
                else:
                    code, body = 404, {"kind": "Status", "apiVersion": "v1", "status": "Failure", "reason": "NotFound", "code": 404}
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        with patch("socket.getfqdn", return_value="localhost"):
            server = ThreadingHTTPServer(("127.0.0.1", 0), API)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        config = {"apiVersion": "v1", "kind": "Config", "current-context": "fixture",
                  "clusters": [{"name": "fixture", "cluster": {"server": f"http://127.0.0.1:{server.server_port}"}}],
                  "contexts": [{"name": "fixture", "context": {"cluster": "fixture", "user": "fixture"}}],
                  "users": [{"name": "fixture", "user": {}}]}
        self.kubeconfig = self.root / "kubeconfig"
        self.kubeconfig.write_text(json.dumps(config))
        self.kubeconfig.chmod(0o600)

    def render(self, agents, *, upgrade=False, succeeds=True):
        values = self.root / "values.json"
        values.write_text(json.dumps({"agents": agents}))
        env = {key: value for key, value in os.environ.items()
               if not key.startswith("HELM_") and key != "KUBECONFIG"}
        env.update(HELM_CACHE_HOME=str(self.root / "cache"), HELM_CONFIG_HOME=str(self.root / "config"),
                   HELM_DATA_HOME=str(self.root / "data"))
        command = ["helm", "template", "gitlab-agent-rbac", str(CHART), "--namespace", "gitlab-agent-rbac",
                   "--kubeconfig", str(self.kubeconfig), "--dry-run=server", "--disable-openapi-validation",
                   "--values", str(values)] + (["--is-upgrade"] if upgrade else [])
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
        if not succeeds:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Forbidden", result.stderr)
            return
        self.assertEqual(result.returncode, 0, result.stderr)
        return [obj for obj in yaml.safe_load_all(result.stdout) if obj]

    def test_missing_namespaces_are_created_once_without_agent_or_release_duplicates(self):
        objects = self.render({"agent-a": {"namespaces": ["shared", "shared", "agent-b", "gitlab-agent-rbac"]},
                               "agent-b": {"namespaces": ["shared", "app-b"]}})
        namespaces = [obj for obj in objects if obj["kind"] == "Namespace"]
        self.assertCountEqual([obj["metadata"]["name"] for obj in namespaces], ["agent-a", "agent-b", "shared", "app-b"])
        for obj in namespaces:
            if obj["metadata"]["name"] in ("shared", "app-b"):
                self.assertEqual(obj["metadata"]["annotations"]["helm.sh/resource-policy"], "keep")

    def test_preexisting_namespaces_are_not_adopted(self):
        for annotations in (None, {}, {"meta.helm.sh/release-name": "another-release", "meta.helm.sh/release-namespace": "gitlab-agent-rbac"},
                            {"meta.helm.sh/release-name": "gitlab-agent-rbac", "meta.helm.sh/release-namespace": "another-namespace"}):
            with self.subTest(annotations=annotations):
                self.existing["app"] = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "app", "annotations": annotations}}
                objects = self.render({"agent": {"namespaces": ["app"]}})
                self.assertEqual([obj["metadata"]["name"] for obj in objects if obj["kind"] == "Namespace"], ["agent"])

    def test_namespaces_owned_by_this_release_remain_managed_on_upgrade(self):
        self.existing["app"] = {"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": "app", "annotations": {
            "meta.helm.sh/release-name": "gitlab-agent-rbac", "meta.helm.sh/release-namespace": "gitlab-agent-rbac"}}}
        objects = self.render({"agent": {"namespaces": ["app"]}}, upgrade=True)
        namespace = next(obj for obj in objects if obj["kind"] == "Namespace" and obj["metadata"]["name"] == "app")
        self.assertEqual(namespace["metadata"]["annotations"]["helm.sh/resource-policy"], "keep")

    def test_lookup_errors_are_not_treated_as_missing_namespaces(self):
        self.denied.add("app")
        self.render({"agent": {"namespaces": ["app"]}}, succeeds=False)


if __name__ == "__main__":
    unittest.main()
