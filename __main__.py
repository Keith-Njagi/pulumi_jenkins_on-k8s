"""A Kubernetes Python Pulumi program"""

import pulumi
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs, DeploymentInitArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, ContainerPortArgs, HTTPGetActionArgs, Namespace, NamespaceInitArgs, ServiceInitArgs, ServiceAccount, PodSpecArgs, PodTemplateSpecArgs, PodSecurityContextArgs, ProbeArgs, Service, ServiceSpecArgs, ServicePortArgs, PersistentVolume, PersistentVolumeSpecArgs, PersistentVolumeClaim, PersistentVolumeClaimSpecArgs, VolumeNodeAffinityArgs, NodeSelectorArgs, NodeSelectorTermArgs, NodeSelectorRequirementArgs
from pulumi_kubernetes.rbac.v1 import ClusterRoleBinding, ClusterRole, ClusterRoleInitArgs, RoleRefArgs, SubjectArgs
from pulumi_kubernetes.storage.v1 import StorageClass, StorageClassInitArgs

# Create a Namespace
namespace = Namespace(
        "jenkins", 
        NamespaceInitArgs(kind="Namespace", api_version="v1", metadata=ObjectMetaArgs(name="devops-tools"))
        )

# Create a Cluster Role
cluster_role = ClusterRole(
        "jenkins-admin",
        ClusterRoleInitArgs(
            kind="ClusterRole",
            api_version="rbac.authorization.k8s.io/v1",
            metadata=ObjectMetaArgs(name="jenkins-admin"),
            rules=[
                { "apiGroups": [""], "resources": ["*"], "verbs": ["*"] },
            ]
        )    
    )

# Create a Service Account
service_account = ServiceAccount(
        "jenkins-admin",
        kind="ServiceAccount",
        api_version="v1",
        metadata=ObjectMetaArgs(name="jenkins-admin", namespace="devops-tools")
    )

# Create a ClusterRoleBinding
cluster_role_binding = ClusterRoleBinding(
        "jenkins-admin",
        kind="ClusterRoleBinding",
        api_version="rbac.authorization.k8s.io/v1",
        metadata=ObjectMetaArgs(name="jenkins-admin"),
        role_ref=RoleRefArgs(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="jenkins-admin"
        ),
        subjects=[SubjectArgs(
            kind="ServiceAccount",
            name="jenkins-admin",
            namespace="devops-tools"
        ),]
    )

# Create a Storage Class
storage_class = StorageClass(
        "local-storage",
        StorageClassInitArgs(
            kind="StorageClass",
            api_version="storage.k8s.io/v1",
            metadata=ObjectMetaArgs(name="local-storage"),
            provisioner="kubernetes.io/no-provisioner",
            volume_binding_mode="WaitForFirstConsumer"
        ),
    )

# Create a Persistent Volume
persistent_volume = PersistentVolume(
        "jenkins-pv-volume",
        kind="PersistentVolume",
        api_version="v1",
        metadata=ObjectMetaArgs(
            name="jenkins-pv-volume",
            labels={"type": "local"}
        ),
        spec=PersistentVolumeSpecArgs(
            storage_class_name="local-storage",
            claim_ref=ObjectMetaArgs(name="jenkins-pv-claim", namespace="devops-tools"),
            capacity={"storage": "10Gi"},
            access_modes=["ReadWriteOnce"],
            local={"path":"/mnt"},
            node_affinity=VolumeNodeAffinityArgs(
                required=NodeSelectorArgs(
                    node_selector_terms=[
                        NodeSelectorTermArgs(
                            match_expressions=[
                                NodeSelectorRequirementArgs(
                                    key="kubernetes.io/hostname", 
                                    operator="In",
                                    values=["minikube"]
                                )
                            ]
                        )
                    ]
                )
            )
        )
    )

# Create a Persistent Volume Claim
persistent_volume_claim = PersistentVolumeClaim(
        "jenkins-pv-claim",
        kind="PersistentVolumeClaim",
        api_version="v1",
        metadata=ObjectMetaArgs(name="jenkins-pv-claim", namespace="devops-tools"),
        spec=PersistentVolumeClaimSpecArgs(
            access_modes=["ReadWriteOnce"],
            resources={"requests": {"storage": "3Gi"}},
            storage_class_name="local-storage"
        )
    )

app_labels = { "app": "jenkins-server" }

# Create a Deployment
deployment = Deployment(
        "jenkins",
        DeploymentInitArgs(
            kind="Deployment",
            api_version="apps/v1",
            metadata=ObjectMetaArgs(
                labels=app_labels,
                name="jenkins",
                namespace="devops-tools"
            ),
            spec=DeploymentSpecArgs(
                replicas=1,
                selector=LabelSelectorArgs(match_labels=app_labels),
                template=PodTemplateSpecArgs(metadata=ObjectMetaArgs(labels=app_labels),
                spec=PodSpecArgs(
                    security_context= PodSecurityContextArgs(fs_group=1000, run_as_user=1000),
                    service_account_name="jenkins-admin",
                    containers=[ContainerArgs(
                        name="jenkins",
                        image="jenkins/jenkins:lts",
                        ports=[
                            ContainerPortArgs(container_port=8080, name="httpport"),
                            ContainerPortArgs(container_port=50000, name="jniport"),
                            ],
                        liveness_probe=ProbeArgs(
                            http_get=HTTPGetActionArgs(path="/login", port=8080),
                            initial_delay_seconds=90,
                            timeout_seconds=5,
                            period_seconds=10,
                            failure_threshold=5,
                        ),
                        readiness_probe=ProbeArgs(
                            http_get=HTTPGetActionArgs(path="/login", port=8080),
                            initial_delay_seconds=60,
                            timeout_seconds=5,
                            period_seconds=10,
                            failure_threshold=3,
                        ),
                        volume_mounts=[{"name": "jenkins-data", "mount_path": "/var/jenkins_home"}],
                    ),],
                    volumes=[{"name": "jenkins-data", "persistent_volume_claim": {"claim_name": "jenkins-pv-claim"}}]
                ),
            )
        )
    ),
)

# Create a Service
service = Service(
        "jenkins-service",
        ServiceInitArgs(
            kind="Service",
            api_version="v1",
            metadata=ObjectMetaArgs(
                name="jenkins-service",
                namespace="devops-tools",
                annotations={"prometheus.io/scrape": "true", "prometheus.io/port": "8080", "prometheus.io/path": "/"},
            ),
            spec=ServiceSpecArgs(
                selector=app_labels,
                ports=[ServicePortArgs(port=8080, target_port=8080, node_port=32000, protocol="TCP")],
                type="NodePort"
            ),
        ),
    )

# pulumi.export("namespace", namespace)
# pulumi.export("deployment", deployment) 

pulumi.export("namespace", namespace.metadata["name"])
pulumi.export("service_account", service_account.metadata["name"])
pulumi.export("cluster_role", cluster_role.metadata["name"])
pulumi.export("cluster_role_binding", cluster_role_binding.metadata["name"])
pulumi.export("storage_class", storage_class.metadata["name"])
pulumi.export("persistent_volume", persistent_volume.metadata["name"])
pulumi.export("persistent_volume_claim", persistent_volume_claim.metadata["name"])
pulumi.export("deployment", deployment.metadata["name"])
pulumi.export("service", service.metadata["name"])

# kubectl port-forward --namespace jenkins  deployment/nginx 9100:80
