#!/usr/bin/env bash
# Author: Erik Olander
# 

help()
{
    echo "will list containers terminated in the last t hours"
    echo "Usage: container_restarts.sh -t 1"
    exit 1
}

while getopts 't:h' OPT; do
    case $OPT in
        t) hours="$OPTARG";;
        h) help;;
        ?) help;;
    esac
done

kubectl get pods -A  -ojson | jq ' .items[]? | select( .metadata.ownerReferences[].kind != "Job" ) | {  node: .spec.nodeName, namespace: .metadata.namespace, pod: .metadata.name, container: .status.containerStatuses[].name , terminated: .status.containerStatuses[].lastState.terminated  , state: .status.containerStatuses[].state  , restartCount: .status.containerStatuses[].restartCount } | select ( (.terminated.finishedAt | fromdateiso8601? > now - '$hours'*3600 ) ) '

