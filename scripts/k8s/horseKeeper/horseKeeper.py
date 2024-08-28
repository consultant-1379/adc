#!/lab/pccc_utils/scripts/csdp_python3_venv/bin/python

import sys
import textwrap
from typing import Dict
from kubernetes import client, config
from base64 import b64decode
from kubernetes.client.rest import ApiException
import os
import argparse
import logging
import yaml
import time
import json
import requests

from getpass import getpass, getuser
from bs4 import BeautifulSoup
import urllib.request
import base64
from itertools import chain
import copy

__version__ = "2.2.0"

CA_CERT = "ca.crt"
CLIENT_CERT = "cert.pem"
CLIENT_KEY = "key.pem"
SECRET_ES_CLIENT_CERT = "eric-cnom-server-searchengine-client-cert"
SECRET_ES_CA_CERT = "eric-sec-sip-tls-trusted-root-cert"
GRAFANA_NAMESPACE = "grafana"
GRAFANA_DATASOURCES_CM = "grafana-datasources"
SEARCH_ENGINE_PORT = "9200"
K8S_CLUSTER_ENV = "~/.cnat_env.yaml"
K8S_CNF_SEAR_ENG_SERVICE_NAME = "eric-data-search-engine-tls"
K8S_CNF_SEAR_ENG_SERVICE_PORT = 9200
SEARCH_ENGINE_URL_FORMAT = "{namespace}-{service_name}.ingress.{cluster}.sero.gic.ericsson.se"
K8S_POD_STATUS_RUNNING = 'Running'

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print("#" * int(len(name) + 4))
    print(f'# {name} #')  # Press Ctrl+F8 to toggle the breakpoint.
    print("#" * int(len(name) + 4))


def extract_ns(nsdata):
    return nsdata.metadata.name


def sleep(seconds):
    logging.info("Wait for %s seconds.", seconds)
    time.sleep(seconds)


def check_namespace_exist(namespace, k8s_client):
    ns_list = k8s_client.list_namespace()
    if not list(map(extract_ns, ns_list.items)).__contains__(namespace):
        logging.error("The namespace %s does not exist, skip extracting the cert data.", namespace)
        return False
    return True


def get_namespaces_list(k8s_client):
    ns_list = k8s_client.list_namespace()
    return list(map(extract_ns, ns_list.items))


def parse_secret(name, namespace, k8s_client, output_path):
    if not os.path.exists(output_path):
        os.makedirs(name=output_path, exist_ok=True)

    if not check_namespace_exist(namespace=namespace, k8s_client=k8s_client):
        logging.error("The namespace %s does not exist, skip extracting the cert data.", namespace)
        return

    secret = k8s_client.read_namespaced_secret(name=name, namespace=namespace, pretty='true')
    ssl_data = {}
    if CA_CERT in secret.data:
        filename_ca = output_path + os.sep + namespace + "-" + CA_CERT
        with open(filename_ca, "w", encoding='utf-8') as f:
            f.write(b64decode(secret.data.get(CA_CERT)).decode('utf-8'))
            logging.info("The CA certificate is saved in %s", filename_ca)
            ssl_data[CA_CERT] = b64decode(secret.data.get(CA_CERT)).decode()
    elif CLIENT_CERT in secret.data:
        ssl_data[CLIENT_CERT] = b64decode(secret.data.get(CLIENT_CERT)).decode()
        ssl_data[CLIENT_KEY] = b64decode(secret.data.get(CLIENT_KEY)).decode()
        filename_cert = output_path + os.sep + namespace + "-" + CLIENT_CERT
        filename_key = output_path + os.sep + namespace + "-" + CLIENT_KEY
        with open(filename_cert, "w", encoding='utf-8') as f:
            f.write(b64decode(secret.data.get(CLIENT_CERT)).decode('utf-8'))
            logging.info("The client certificate is saved in %s", filename_cert)
        with open(filename_key, "w", encoding='utf-8') as f:
            f.write(b64decode(secret.data.get(CLIENT_KEY)).decode('utf-8'))
            logging.info("The private key of client certificate is saved in %s", filename_key)
    return ssl_data


def inject_cert_to_datasources(ca, cert, namespace, ds):
    data_sources_key = "datasources"
    secure_json_data_key = "secureJsonData"
    json_data_key = "jsonData"
    for i in range(len(ds[data_sources_key])):
        if "." + namespace + ":" + SEARCH_ENGINE_PORT in ds[data_sources_key][i]["url"]:
            if json_data_key not in ds[data_sources_key][i]:
                logging.warning("The field %s in %s does not exist,initialize it with {}", json_data_key,
                                ds[data_sources_key][i]["name"])
                ds[data_sources_key][i][json_data_key] = {}
            ds[data_sources_key][i][json_data_key]["tlsAuth"] = True
            ds[data_sources_key][i][json_data_key]["tlsAuthWithCACert"] = True
            if secure_json_data_key not in ds[data_sources_key][i]:
                logging.warning("The field %s in %s does not exist,initialize it with {}", secure_json_data_key,
                                ds[data_sources_key][i]["name"])
                ds[data_sources_key][i][secure_json_data_key] = {}
            ds[data_sources_key][i][secure_json_data_key]["tlsCACert"] = ca.get(CA_CERT)
            ds[data_sources_key][i][secure_json_data_key]["tlsClientCert"] = cert.get(CLIENT_CERT)
            ds[data_sources_key][i][secure_json_data_key]["tlsClientKey"] = cert.get(CLIENT_KEY)
    return ds


def check_pods_ready(pod_name_prefix, expected_pod_status, namespace, retry_times, k8s_client_core):
    counter = retry_times
    while counter > 0:
        new_pods = k8s_client_core.list_namespaced_pod(namespace=namespace)
        pods_ready_flag = True
        for pod in new_pods.items:
            if str(pod.metadata.name).startswith(pod_name_prefix):
                if expected_pod_status.lower() == "running":
                    if pod.status is None or pod.status.container_statuses is None:
                        continue
                    containers_ready = list(filter(lambda x: x.ready is True, pod.status.container_statuses))
                    if expected_pod_status.lower() != pod.status.phase.lower() or len(containers_ready) < len(pod.status.container_statuses):
                        pods_ready_flag = False
                        logging.info("The pod %s is NOT Ready,status:%s(%s/%s)", pod.metadata.name,
                                     pod.status.phase, len(containers_ready), len(pod.status.container_statuses))
                elif expected_pod_status.lower() == "completed":
                    if pod.status.phase != 'Succeeded':
                        pods_ready_flag = False
                        logging.info("The pod %s is NOT Ready, status:%s", pod.metadata.name, pod.status.phase)
        if not pods_ready_flag:
            counter = counter - 1
            sleep(10)
        else:
            break
    if counter < 1:
        logging.error("The pods %s-XXX in namespace %s are not ready.", pod_name_prefix, namespace)
        return
    logging.info("The pods %s-XXX in namespace %s are ready.", pod_name_prefix, namespace)


def get_pod_status(pod):
    containers_ready = list(filter(lambda x: x.ready is True, pod.status.container_statuses))
    return str.format("%s(%s/%s", pod.status.phase, len(containers_ready), len(pod.status.container_statuses))


def restart_pods(pod_name_prefix, namespace, k8s_client_core):
    pods = k8s_client_core.list_namespaced_pod(namespace=namespace)
    for pod in pods.items:
        if str(pod.metadata.name).startswith(pod_name_prefix):
            logging.info("Restart pod:%s in namesapce %s", pod.metadata.name, namespace)
            k8s_client_core.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

    sleep(10)
    check_pods_ready(pod_name_prefix=pod_name_prefix, expected_pod_status=K8S_POD_STATUS_RUNNING, namespace=namespace,
                     retry_times=3, k8s_client_core=k8s_client_core)


def patch_cm_config(name, namespace, cnf_namespace_list, cert_output_path):
    cm_data = client_core_v1.read_namespaced_config_map(name=name, namespace=namespace)
    datasources = yaml.full_load(cm_data.data.get("datasource.yaml"))
    for ns in cnf_namespace_list:
        logging.info("Parsing secrets in namespace %s", ns)
        ca_data = parse_secret(name=SECRET_ES_CA_CERT, namespace=ns, k8s_client=client_core_v1,
                               output_path=cert_output_path)
        cert_data = parse_secret(name=SECRET_ES_CLIENT_CERT, namespace=ns, k8s_client=client_core_v1,
                                 output_path=cert_output_path)
        if len(ca_data) == 1 and len(cert_data) == 2:
            datasources = inject_cert_to_datasources(ca_data, cert_data, ns, datasources)
        else:
            logging.error("Failed to get CA certificates or client certificate for %s", ns)

    cm_data.data["datasource.yaml"] = yaml.dump(datasources)
    try:
        client_core_v1.patch_namespaced_config_map(name=GRAFANA_DATASOURCES_CM, namespace=GRAFANA_NAMESPACE,
                                                   body=cm_data)
        logging.info("Patch grafana datasources config map successfully!")
    except ApiException as e:
        logging.error("Failed to patch grafana datasources configmap! %s.", e)


def locate_k8s_kubeconfig(cluster, file_path):
    try:
        with open(file=file_path, mode='r', encoding="utf-8") as f:
            k8s_cluster_data = yaml.full_load(f)
            cluster_list = k8s_cluster_data["cluster_kubeconfig"]
            if cluster not in cluster_list.keys():
                logging.error("Failed to locate the cluster %s \n"
                              "The candidate for the argument '-k' are :%s", cluster, list(cluster_list.keys()))
                sys.exit(1)
            else:
                return cluster_list[cluster]
    except OSError as reason:
        logging.error("Failed to open yaml file %s because %s", file_path, reason)
        return None


def get_clusters_list(file_path):
    try:
        with open(file=file_path, mode='r', encoding="utf-8") as f:
            k8s_cluster_data = yaml.full_load(f)
            cluster_list = k8s_cluster_data["cluster_kubeconfig"]
            return list(cluster_list.keys())
    except OSError as reason:
        logging.error("Failed to open yaml file %s because %s", file_path, reason)
        return None


def create_k8s_ingresses(cnf_namespace_list, backend_service_name, backend_service_port, cluster,
                         k8s_client_netw, k8s_client_core):
    ingress_name = backend_service_name
    for cnf_namespace in cnf_namespace_list:
        if not check_namespace_exist(namespace=cnf_namespace, k8s_client=k8s_client_core):
            logging.error("The namespace %s does not exist, skip creating the ingress.", cnf_namespace)
            return False

        # check if the ingress already exist
        try:
            fetched_ingresses = client_netw_v1.list_namespaced_ingress(namespace=cnf_namespace,
                                                                       field_selector='metadata.name='
                                                                                      + ingress_name)
        except ApiException as e:
            logging.error("Failed to query the ingress %s in namespace %s %s", ingress_name, cnf_namespace, e)
            return False
        if len(fetched_ingresses.items) > 0:
            logging.warning("Can't create ingress %s in namespace %s as it already exists, "
                            "better to check its content!", ingress_name, cnf_namespace)
            continue

        url = SEARCH_ENGINE_URL_FORMAT.format(namespace=cnf_namespace, cluster=cluster,
                                              service_name=backend_service_name)
        logging.info("Create ingress %s in %s, backend service:%s:%s, url:%s", ingress_name,
                     cnf_namespace, backend_service_name, backend_service_port, url)
        annotations: Dict[str, str] = {'kubernetes.io/ingress.class': 'nginx',
                                       'nginx.ingress.kubernetes.io/backend-protocol': 'HTTPS',
                                       'nginx.ingress.kubernetes.io/ssl-passthrough': 'true'}

        metadata = client.V1ObjectMeta(annotations=annotations, namespace=cnf_namespace, name=ingress_name)
        spec_rules_http_paths_backend = client.V1IngressBackend(
            service=client.V1IngressServiceBackend(name=backend_service_name,
                                                   port=client.V1ServiceBackendPort(number=backend_service_port)),
            resource=None)
        spec_rules_http_paths = [client.V1HTTPIngressPath(backend=spec_rules_http_paths_backend, path='/',
                                                          path_type='ImplementationSpecific')]
        spec_rules = [client.V1IngressRule(host=url, http=client.V1HTTPIngressRuleValue(paths=spec_rules_http_paths))]
        spec_tls = [client.V1IngressTLS(hosts=[url])]
        spec = client.V1IngressSpec(rules=spec_rules, tls=spec_tls)
        ingress_body = client.V1Ingress(api_version='networking.k8s.io/v1', kind='Ingress', metadata=metadata,
                                        spec=spec)
        try:
            k8s_client_netw.create_namespaced_ingress(namespace=cnf_namespace, body=ingress_body)
        except ApiException as e:
            logging.error("Failed to create ingress %s in namespace %s %s", ingress_name, cnf_namespace, e)
            return False

    return True


def set_cnf_max_buckets(max_buckets, cnf_namespace_list, backend_service_name, cluster, k8s_client_core,
                        cert_output_path):
    for cnf_namespace in cnf_namespace_list:
        logging.info("set search engine max_buckets for cnf %s", cnf_namespace)
        parse_secret(name=SECRET_ES_CA_CERT, namespace=cnf_namespace, k8s_client=k8s_client_core,
                     output_path=cert_output_path)
        parse_secret(name=SECRET_ES_CLIENT_CERT, namespace=cnf_namespace, k8s_client=k8s_client_core,
                     output_path=cert_output_path)

        filename_cert = cert_output_path + os.sep + cnf_namespace + "-" + CLIENT_CERT
        filename_key = cert_output_path + os.sep + cnf_namespace + "-" + CLIENT_KEY

        url = SEARCH_ENGINE_URL_FORMAT.format(namespace=cnf_namespace, cluster=cluster,
                                              service_name=backend_service_name)
        api_url = 'https://' + url + ':443' + '/_cluster/settings'
        headers = {'Content-type': 'application/json'}
        data = {"persistent": {"search": {"max_buckets": max_buckets}}}
        json_data = json.dumps(data)

        with requests.Session() as s:
            resp = s.put(url=api_url, headers=headers, data=json_data, verify=False, cert=(filename_cert, filename_key))
            content = json.loads(resp.content.decode('utf-8'))
            if resp.status_code == 200 and content['acknowledged']:
                logging.info("Update search engine max_buckets for %s successfully.", cnf_namespace)
            else:
                logging.error("Failed to update search engine max_buckets for %s, status code:%s, content:%s",
                              cnf_namespace, resp.status_code, content)


def get_critical_pods_from_jira():
    url = "https://pdupc-jira.internal.ericsson.com/browse/PCVTC-3346"
    user = getuser()
    password = getpass()
    request = urllib.request.Request(url)
    base64string = base64.b64encode(bytes('%s:%s' % (user, password), 'ascii'))
    request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
    result = urllib.request.urlopen(request)
    html = result.read()

    soup = BeautifulSoup(html, features="html.parser")

    # interesting info has td (table division?)
    criticalPods = []
    product = pod = ""
    items = soup.find_all('td')
    increment = False
    for i in range(5, len(soup.find_all('td'))):
        # jira has been updated with a new column with the old name of the pod
        # probably this code could be nicer
        if increment == True:
            i = i + 2
            increment = False
        # only the cell with product has a dot
        if "." in items[i].text:
            product = items[i + 1].text
            # product = re.search("[0-9]+.\s([A-Z]+)", items[i+1].text).group(1).lower()
        # all critical pods start with "eric"
        if "eric" in items[i].text:
            pod = items[i].text
            increment = True
        if product and pod:
            criticalPods.append((product.lower(), pod))
            product = pod = ""

    print("Number of critical pods from Jira: {}".format(len(criticalPods)))
    print(criticalPods)
    return criticalPods


def set_k8s_nodes_unscheduled(unschedulable, worker_node_name_list, k8s_client):
    if unschedulable:
        action_name = "Cordon"
    else:
        action_name = "Uncordon"

    logging.info("%s worker nodes: %s", action_name, worker_node_name_list)

    body = {
        "spec": {
            "unschedulable": unschedulable,
        },
    }

    for name in worker_node_name_list:
        k8s_client.patch_node(name, body)

    # check worker node schedule status
    sleep(1)
    counter = 10
    flag = True
    while counter > 0:
        for name in worker_node_name_list:
            node = k8s_client.read_node(name)
            if (unschedulable and not node.spec.unschedulable) or \
                    (not unschedulable and node.spec.unschedulable is not None):
                flag = False
                break
        if not flag:
            logging.warning("The worker node %s are not in the wanted status, the current unschedulable is %s", name,
                            node.spec.unschedulable)
            flag = True
            counter = counter - 1
            sleep(3)
        else:
            break

    if counter == 0:
        logging.error("Failed to %s worker nodes.", action_name.lower())
        return False

    logging.info("%s worker nodes successfully.", action_name)
    return True


def do_critical_pods_data_cleaning(excluded_pods, critical_pods, all_pods):
    if excluded_pods is not None:
        sep = ':'
        for excluded_pod in excluded_pods:
            if sep not in excluded_pod:
                logging.error(
                    "Wrong value format for argument '--excludePods', content should be like pcg:eric-pc-up-data-plane")
                exit(1)
            namespace = excluded_pod.split(sep)[0]
            pod_prefix = excluded_pod.split(sep)[1]
            if (namespace, pod_prefix) in critical_pods:
                logging.info("Exclude pod:%s", (namespace, pod_prefix))
                critical_pods.remove((namespace, pod_prefix))
            else:
                logging.warning("The pod %s to exclude is not in the critical pod list", excluded_pod)

    all_pods_tidy = list(map(lambda pod: (pod.metadata.namespace.lower(), pod.metadata.name), all_pods.items))
    critical_pod_backup = copy.deepcopy(critical_pods)
    for critical_pod in critical_pod_backup:
        found = False
        for pod_tidy in all_pods_tidy:
            if str(pod_tidy[0]).startswith(critical_pod[0]) and str(pod_tidy[1]).startswith(critical_pod[1]):
                found = True
                break
        if not found:
            logging.warning("Remove the pod %s item from the planned critical pod list "
                            "as it's not deployed on target k8s cluster.", critical_pod)
            critical_pods.remove(critical_pod)

    logging.info("Number of critical pods after filtered:%s \n %s", len(critical_pods), critical_pods)


def delete_running_pods(critical_pods_to_move, all_pods, k8s_client):
    move_counter = 0
    for item in critical_pods_to_move:
        for pod in all_pods.items:
            pod_name = pod.metadata.name
            namespace = pod.metadata.namespace.lower()
            k8s_resource_kind = pod.metadata.owner_references[0].kind
            if str(namespace).startswith(item[0]) and str(pod_name).startswith(item[1]):
                if k8s_resource_kind != 'DaemonSet':
                    if 'eric-pc-up-data-plane' not in pod_name:
                        logging.info("Move pod:%s in namespace:%s", pod_name, namespace)
                        move_counter = move_counter + 1
                        k8s_client.delete_namespaced_pod(pod_name, namespace)
                        if k8s_resource_kind == "StatefulSet":
                            sleep(15)
                        else:
                            sleep(5)
                        check_pods_ready(pod_name_prefix=item[1], expected_pod_status=K8S_POD_STATUS_RUNNING,
                                         namespace=namespace, retry_times=10, k8s_client_core=k8s_client)
                    else:
                        logging.warning(
                            "Don't have to move pod eric-pc-up-data-plane as they are deployed in seperate pool")

                break

    return move_counter


def move_critical_pods(worker_nodes_number, critical_pods, excluded_pods, k8s_client):
    """ move_critical_pods

        Move the critical pods to the <worker_nodes_number> woker nodes by cordon/uncordon and delete pod

        :param worker_nodes_number: the planned worker nodes number on which run all the critical pods
        :param List critical_pods: List of tuple (<NAMESPACE>, <POD-PREFIX>)
        :param excluded_pods: the critical pods that don't have to move
        :param CoreV1Api k8s_client: The k8s client sends kubectl commands to k8s cluster
        :return:
        """

    logging.info("Get the pods of all the namespace in k8s cluster, it may take several seconds.")
    all_pods = k8s_client.list_pod_for_all_namespaces()

    do_critical_pods_data_cleaning(excluded_pods=excluded_pods, critical_pods=critical_pods, all_pods=all_pods)
    picked_worker_nodes = fetch_worker_nodes_with_critical_pods(worker_nodes_number, critical_pods, all_pods)
    critical_pods_to_move = get_critical_pods_to_move(picked_worker_nodes=picked_worker_nodes,
                                                      critical_pods=critical_pods)

    if len(critical_pods_to_move) < 1:
        logging.info("No need to move pods as the picked worker nodes have all the wanted critical pods.")
        logging.info("The picked worker nodes:\n %s", list(map(lambda x: x[0], picked_worker_nodes)))
    else:
        # get all the k8s nodes from the target k8s cluster
        all_k8s_nodes = k8s_client.list_node().items
        picked_worker_node_name_list = list(map(lambda x: x[0], picked_worker_nodes))
        k8s_node_name_list = list(map(lambda x: x.metadata.name, all_k8s_nodes))
        k8s_node_name_list_to_cordon = list(filter(
            lambda x: x not in picked_worker_node_name_list and not x.__contains__('master'), k8s_node_name_list))

        cordon_suc = set_k8s_nodes_unscheduled(unschedulable=True, worker_node_name_list=k8s_node_name_list_to_cordon,
                                               k8s_client=k8s_client)
        if not cordon_suc:
            logging.error("Can't move critical pods as failed to cordon worker nodes")
            exit(1)

        sleep(5)
        logging.info("Start moving %s critical pods to worker nodes:%s", len(critical_pods_to_move),
                     picked_worker_node_name_list)
        move_counter = delete_running_pods(critical_pods_to_move=critical_pods_to_move, all_pods=all_pods,
                                           k8s_client=k8s_client)

        sleep(10)
        set_k8s_nodes_unscheduled(unschedulable=False, worker_node_name_list=k8s_node_name_list_to_cordon,
                                  k8s_client=k8s_client)

        logging.info("Get the pods of all the namespace in k8s cluster, it may take several seconds.")
        all_pods_after_move = k8s_client.list_pod_for_all_namespaces()
        picked_worker_nodes = fetch_worker_nodes_with_critical_pods(worker_nodes_number, critical_pods,
                                                                    all_pods_after_move)
        critical_pods_left = get_critical_pods_to_move(picked_worker_nodes=picked_worker_nodes,
                                                       critical_pods=critical_pods)
        if len(critical_pods_left) < 1:
            logging.info("%s critical pods have been moved successfully.", move_counter)
            logging.info("Congratulations! The picked worker nodes have all the critical pods")
            logging.info("The picked worker nodes:\n %s", list(map(lambda x: x[0], picked_worker_nodes)))
        else:
            logging.error(
                "Too bad, there are still some critical pods out of the picked %s worker nodes:\n %s",
                worker_nodes_number, critical_pods_left)


def get_worker_nodes_with_critical_pods(critical_pods, all_pods):
    """get_worker_nodes_with_critical_pods

    get the worker nodes with critical pods on them

    :param worker_nodes_number: the planned worker nodes number on which run all the critical pods
    :param all_pods: All the running pods list from the target k8s cluster
    :param List critical_pods: List of tuple (<NAMESPACE>, <POD-PREFIX>)
    :param CoreV1Api k8s_client: The k8s client sends kubectl commands to k8s cluster
    :return: Dict, {WORKER-NODE-NAME>:[(<NAMESPACE>, <POD-PREFIX>),...],...}
    """
    worker_node_dict = {}

    for pod in all_pods.items:
        worker_node_name = pod.spec.node_name
        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace.lower()
        for critical_pod in critical_pods:
            if str(namespace).startswith(critical_pod[0]) and str(pod_name).startswith(critical_pod[1]):
                if worker_node_name not in worker_node_dict.keys():
                    worker_node_dict[worker_node_name] = [critical_pod]
                elif critical_pod not in worker_node_dict[worker_node_name]:
                    worker_node_dict[worker_node_name].append(critical_pod)

    for item in worker_node_dict.keys():
        logging.debug("Node name:%s critical-pod-num: %s, details:%s", item, len(worker_node_dict[item]),
                      worker_node_dict[item])

    return worker_node_dict


def fetch_worker_nodes_with_critical_pods(worker_nodes_number, critical_pods, all_pods):
    """fetch_worker_nodes_with_most_critical_pods

    list the top N worker nodes with most critical pods

    :param worker_nodes_number: the planned worker nodes number on which run all the critical pods
    :param all_pods: All the running pods list from the target k8s cluster
    :param List critical_pods: List of tuple (<NAMESPACE>, <POD-PREFIX>)
    :param CoreV1Api k8s_client: The k8s client sends kubectl commands to k8s cluster
    :return: List, [(WORKER-NODE-NAME>,[(<NAMESPACE>, <POD-PREFIX>),...]),...]
             return the picked worker nodes with the critical pods info.
    """
    worker_node_with_critical_dict = get_worker_nodes_with_critical_pods(critical_pods=critical_pods, all_pods=all_pods)
    worker_node_dict_sorted = sorted(worker_node_with_critical_dict.items(), key=lambda x: len(x[1]), reverse=True)

    if len(worker_node_dict_sorted) <= worker_nodes_number:
        res = worker_node_dict_sorted
    else:
        res = worker_node_dict_sorted[:worker_nodes_number]
    for item in res:
        logging.info("The picked worker node:%s with %s critical pods, \nDetails:%s", item[0], len(item[1]),
                     item[1])
    return res


def get_critical_pods_to_move(picked_worker_nodes, critical_pods):
    """get_critical_pods_to_move

    get the critical pods need to move, the critical pods is from the jira case, not the ones that are running on k8s

    :param List picked_worker_nodes: List of (WORKER-NODE-NAME>,[(<NAMESPACE>, <POD-PREFIX>),...])
    :param List critical_pods: List of tuple (<NAMESPACE>, <POD-PREFIX>), it's from the jira case
    :param CoreV1Api k8s_client: The k8s client sends kubectl commands to k8s cluster
    :return: List , the List of tuple (<NAMESPACE>, <POD-PREFIX>)
    """
    critical_pods_to_move = []
    critical_pods_in_place = set(list(chain.from_iterable(list(map(lambda x: x[1], picked_worker_nodes)))))

    logging.info("The number of critical pods no need to move is %s, details:%s", len(critical_pods_in_place),
                 critical_pods_in_place)
    for critical_pod in critical_pods:
        if critical_pod not in critical_pods_in_place:
            critical_pods_to_move.append(critical_pod)
    logging.info("critical_pods_to_move %s", critical_pods_to_move)
    return critical_pods_to_move


def save_critical_pods(worker_node_name, critical_pods, k8s_client):
    logging.info("Save critical pods on worker node %s", worker_node_name)
    logging.info("Get the pods of all the namespace in k8s cluster, it may take several seconds.")
    all_pods = k8s_client.list_pod_for_all_namespaces()
    # logging.info("pod info:%s", all_pods.items[0])
    for pod in all_pods.items:
        pod_name = pod.metadata.name
        namespace = pod.metadata.namespace.lower()
        logging.info("node:%s, namesapce:%s pod-name:%s", pod.spec.node_name, namespace, pod_name)
        logging.info("node:%s, namesapce:%s pod-name:%s status:%s", pod.spec.node_name, namespace, pod_name, get_pod_status(pod))

    # do_critical_pods_data_cleaning(excluded_pods=[], critical_pods=critical_pods, all_pods=all_pods)


if __name__ == '__main__':
    print_hi(
        'horseKeeper, The SUPER Assistant')
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

    arg_parser = argparse.ArgumentParser(description="horseKeeper Version:" + __version__,
                                         usage=textwrap.dedent(
                                             '''\
                                             
                                             Example: 
                                             > horseKeeper -k n99-eccd1 -n sc ccsm --patch-grafana-ds --cnf-max-buckets 262143
                                             \n'''))

    group = arg_parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--cluster', '-k', type=str,
                       default="n99-eccd1", required=False,
                       help="the target k8s traffic cluster on which the grafana and CNFs are running. "
                            "for example n99-eccd1")

    group.add_argument('--list-clusters', '-l', action='store_true', dest='list_clusters',
                       help="list the candidate clusters for argument '-k'")

    arg_parser.add_argument('--cnf-namespaces', '-n', type=str, nargs="+", required=False,
                            help="the involved CNF namespace list.")
    arg_parser.add_argument('--patch-grafana-ds', '-p', action='store_true', dest='patch_grafana_ds',
                            help="patch the grafana datasource configmap for search engine query.")
    arg_parser.add_argument('--cnf-max-buckets', '-b', type=str, dest='max_buckets',
                            help="set the CNF search engine max-buckets value(create ingress if not exist).")
    arg_parser.add_argument('--create-ingress-search-engine-tls', '-s', action='store_true',
                            dest='create_ingress_search_eng_tls',
                            help="create CNF tls search engine ingresses.")
    arg_parser.add_argument('--output', '-o', type=str, required=False,
                            help="(optional) the target path for saving the output data files.")

    arg_parser.add_argument('--worker-nodes-number', '-w', type=int, dest='worker_nodes_num',
                            help="Move all the critical pods to the <worker-nodes-number> worker nodes.")

    arg_parser.add_argument('--excludePods', type=str, nargs="*", required=False,
                            help="with '-w', add the pods that don't have to move."
                                 "for example pcg:eric-pc-up-data-plane")

    arg_parser.add_argument('--save-critical-pods-on-worker', '-c', type=str, dest='worker_node_with_critical',
                            help='Save the detailed critical pods data on one worker node to a file.')

    arg_parser.add_argument('--version', '-v', action='store_true',
                            help="Show the version.")

    args = arg_parser.parse_args()
    if args.list_clusters:
        logging.info("The candidate clusters list for argument '-k':\n %s",
                     get_clusters_list(file_path=os.path.expanduser(K8S_CLUSTER_ENV)))
        exit(0)

    config.load_kube_config(locate_k8s_kubeconfig(cluster=args.cluster, file_path=os.path.expanduser(K8S_CLUSTER_ENV)))
    client_core_v1 = client.CoreV1Api()
    client_netw_v1 = client.NetworkingV1Api()

    if args.version:
        print(__version__)
        exit(0)

    if args.cnf_namespaces is None and (
            args.patch_grafana_ds or args.create_ingress_search_eng_tls or args.max_buckets):
        logging.error("None of CNF namespce is picked! the candidate ones on cluster %s:\n%s", args.cluster,
                      get_namespaces_list(client_core_v1))
        exit(1)

    if args.output is None:
        certs_output_path = "./certs-" + args.cluster
    else:
        certs_output_path = args.output

    if args.patch_grafana_ds:
        patch_cm_config(name=GRAFANA_DATASOURCES_CM, namespace=GRAFANA_NAMESPACE,
                        cnf_namespace_list=args.cnf_namespaces,
                        cert_output_path=certs_output_path)

        restart_pods(pod_name_prefix="grafana", namespace=GRAFANA_NAMESPACE, k8s_client_core=client_core_v1)

    if args.create_ingress_search_eng_tls:
        create_k8s_ingresses(cnf_namespace_list=args.cnf_namespaces, backend_service_name=K8S_CNF_SEAR_ENG_SERVICE_NAME,
                             backend_service_port=K8S_CNF_SEAR_ENG_SERVICE_PORT, cluster=args.cluster,
                             k8s_client_netw=client_netw_v1, k8s_client_core=client_core_v1)

    if args.max_buckets is not None:
        ingress_res = create_k8s_ingresses(cnf_namespace_list=args.cnf_namespaces,
                                           backend_service_name=K8S_CNF_SEAR_ENG_SERVICE_NAME,
                                           backend_service_port=K8S_CNF_SEAR_ENG_SERVICE_PORT, cluster=args.cluster,
                                           k8s_client_netw=client_netw_v1, k8s_client_core=client_core_v1)
        if ingress_res:
            logging.info("Sleep 6 seconds for all the ingresses are ready.")
            sleep(6)
            set_cnf_max_buckets(max_buckets=args.max_buckets, cnf_namespace_list=args.cnf_namespaces,
                                backend_service_name=K8S_CNF_SEAR_ENG_SERVICE_NAME,
                                cluster=args.cluster,
                                k8s_client_core=client_core_v1, cert_output_path=certs_output_path)

        else:
            logging.error("Can't set the search engine max_buckets as no ingress is available.")

    if args.worker_nodes_num is not None:
        move_critical_pods(worker_nodes_number=args.worker_nodes_num, critical_pods=get_critical_pods_from_jira(),
                           excluded_pods=args.excludePods, k8s_client=client_core_v1)

    if args.worker_node_with_critical is not None:
        save_critical_pods(worker_node_name=args.worker_node_with_critical, critical_pods="", k8s_client=client_core_v1)

    if (args.max_buckets is None and not args.create_ingress_search_eng_tls and not args.patch_grafana_ds) \
            and not args.list_clusters and not args.worker_nodes_num and not args.worker_node_with_critical:
        logging.warning("horseKeeper is doing nothing, please consider making more arguments involved.")
