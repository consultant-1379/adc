# check critical pods from kubectl get pod log file
function check_critical_pods()
{
  local critical_pods_file get_pod_logfile restart_worker
  critical_pods_file=$1
  get_pod_logfile=$2
  restart_worker=$3
  res=""
  while read line
  do
    ns=$(echo $line | awk '{print $1}' | tr A-Z a-z)
    pod=$(echo $line | awk '{print $2}')
    if [[ "$restart_worker" ]];then
      output=$(grep -E "$ns[[:space:]]+$pod" $get_pod_logfile | grep $restart_worker | awk '{print $1,$2}' || true)
      [[ $output ]] && res+="$output\n"
    else
      output=$(grep -E "$ns[[:space:]]+$pod" $get_pod_logfile | awk '{print $1,$2,$(NF-2)}' || true)
      [[ $output ]] && res+="$output\n"
    fi
  done < $critical_pods_file
  printf "$res" | column -t
}
