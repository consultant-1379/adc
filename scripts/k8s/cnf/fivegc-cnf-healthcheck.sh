#-------------------------------------------------------------------------------------------
# Description: The script is for CNF Healthcheck on ECCD Traffic Cluster Director server.
# Author     : dekuan.kong@ericsson.com
# version    : 1.2                                                                          
# Reference  : CCXX CPI Health Check : 
#              http://calstore.internal.ericsson.com/elex?LI=EN/LZN7020554/1R39A&FB=0_0&FN=1_1553-CSH109714_1Uen.A.html&HT=kew1582634238776__ul_a4z_rcn_g3b
#-------------------------------------------------------------------------------------------

#!/usr/bin/env bash


##############################################################################
########### run the script on Traffic Cluster Director for 5GC CNF Healthcheck###
##############################################################################
VERSION=1.2

# 0: don't collect pod log when CNF in unhealthy state
# 1: Collect pod log when CNF in unhealthy state 
COLLECT_POD_LOG_FLAG=0
##### Functions definitions 

# background color
BG_RED="41"
BG_GREEN="42"
BG_YELLOW="43"
BG_BLUE="44"
BG_VIOLET="45"
BG_SKYBLUE="46"
BG_WHITE="47"

function debug()
{
    echo -e "\033[37m$1\033[0m"
}
function log_info()
{
    echo -e "\033[32m$1\033[0m"
}
function warn()
{
    echo -e "\033[33m$1\033[0m"
}
function log_error()
{
    echo -e "\033[31m$1\033[0m"
}


function usage() {
  echo;
  log_info 'Description: Run it on eccd cluster for cnf HealthCheck.'
  log_info 'usage: ./fivegc_cnf_healthcheck.sh <namespace> <testing Description>'
  log_info 'usage:Example: ./fivegc_cnf_healthcheck.sh ccdm or ./fivegc_cnf_healthcheck.sh ccdm "before work node reboot"'
  echo;
}

# output the result information for each Healthcheck item
# param : the core information to output 
function format_slogan() {
  datetime=`date "+%Y-%m-%d %H:%M:%S"`
  ret_info=$*
  len=`expr $(echo $ret_info | awk '{print length($0)}') + 30 `
  echo |tee -a  $REPORT_FILE
  seq -s "*" ${len}|sed -E "s/[0-9]//g" |tee -a $REPORT_FILE
  echo "***" ${ret_info} " ${datetime} ***"   |tee -a $REPORT_FILE
  seq -s "*" ${len}|sed -E "s/[0-9]//g" |tee -a $REPORT_FILE

}



# check_alarms <namespace>
# return : ret 0:no alarm;  1:at least one alarm exists
function check_alarms() {
  format_slogan "start checking alarms for $1"
  if [ $# -ne 1 ]
  then 
    echo "### Check_alarms:FAIL, Param is wrong" |tee -a $REPORT_FILE 
    ret=1
  else
    CNF_NS=$1
    
    alarms_list=$(kubectl -n ${CNF_NS} exec -it $(kubectl -n ${CNF_NS} get pods -l app=eric-fh-alarm-handler | grep -v topics | tail -1 | awk '{print $1}') -c eric-fh-alarm-handler -- ah_alarm_list.sh -f | tee -a $REPORT_FILE)
    echo "### check_alarms ${CNF_NS}-->alarm_list:${alarms_list} "
    alarm_exists=$(echo $alarms_list |grep -i alarmName)
    if [[ $alarm_exists == "" ]]
    then
	log_info "### check_alarms $CNF_NS : No alarm found, Good!" |tee -a $REPORT_FILE
        return 0
    else
        log_error "Alarm list:$alarms_list"
        return 1	
    fi
  fi

  return $ret
  
}

#Description : the Function is only for checking CCDM UDR relative status 
#Param       : The name of the ccdm namespace
function check_ccdm_udr_system_status() {
  ccdm_ns=$1
  ret=0
  format_slogan "Check CCDM UDR Operational State."

  url_config_prefix="http://localhost:5003/cm/api/v1/configurations/"
  operate_state=$(kubectl exec --namespace $ccdm_ns  $(kubectl get pods --namespace $ccdm_ns |egrep -m 1 "eric-cm-mediator-[a-f,0-9]"|awk '{print $1}')  -- curl -s ${url_config_prefix}ericsson-udr | jq -r '.data."ericsson-udr:udr"."operational-state"'|tee -a $REPORT_FILE )
  if [ "$operate_state" = "enabled" ]
  then
    log_info "The UDR Operational State is enabled." | tee -a $REPORT_FILE
  else
    log_error "The UDR Operational State is NOT enabled." | tee -a $REPORT_FILE
    ret=1
  fi

  format_slogan "Check CCDM UDR Administrative State."
  admin_state=$(kubectl exec --namespace $ccdm_ns  $(kubectl get pods --namespace $ccdm_ns |egrep -m 1 "eric-cm-mediator-[a-f,0-9]"|awk '{print $1}')  -- curl -s ${url_config_prefix}ericsson-udr | jq -r '.data."ericsson-udr:udr"."administrative-state"'|tee -a $REPORT_FILE )
  if [ "$admin_state" = "unlocked" ]
  then
    log_info "The UDR Administrative State is unlocked." | tee -a $REPORT_FILE
  else
    log_error "The UDR Administrative State is NOT unlocked." | tee -a $REPORT_FILE
    ret=1
  fi

  format_slogan "Check CCDM UDR Availability Errors."
  aval_error=$(kubectl exec --namespace $ccdm_ns  $(kubectl get pods --namespace $ccdm_ns |egrep -m 1 "eric-cm-mediator-[a-f,0-9]"|awk '{print $1}')  -- curl -s ${url_config_prefix}ericsson-udr | jq -r '.data."ericsson-udr:udr"."availability-error"'|tee -a $REPORT_FILE )
  if [ "$aval_error" = "[]" ]
  then
    log_info "The UDR Availability Errors: NO ERROR." | tee -a $REPORT_FILE
  else
    log_error "The UDR Availability Errors. ERROR EXISTS: ${aval_error}" | tee -a $REPORT_FILE
    ret=1
  fi

  format_slogan "Check CCDM UDR System status."
  url_prefix="-- curl http://localhost:8080/udr-status/v1/tree?path=/udr/"
 
  format_slogan "Check CCDM UDR System status." 
  # refer to CCDM CPI   
  items_name_list[0]="Check UDR status"
  items_name_list[1]="Check message bus status"
  items_name_list[2]="Check Nudr FE status"
  items_name_list[3]="Check LDAP FE status"
  items_name_list[4]="Check LDAP Balancer status"
  items_name_list[5]="Check SOAP Notifchecker status"
  items_name_list[6]="Check SOAP Notifsender status"
  items_name_list[7]="Check REST Notifchecker status"
  items_name_list[8]="Check REST Notifsender status"
  items_name_list[9]="Check DBmanager status"
  items_name_list[10]="Check DBmonitor status"


  items_url_list[0]="status"
  items_url_list[1]="reporting/messageBusMonitor"
  items_url_list[2]="reporting/nudrFe"
  items_url_list[3]="reporting/ldapFe"
  items_url_list[4]="reporting/ldapBalancer"
  items_url_list[5]="reporting/SOAPnotifchecker"
  items_url_list[6]="reporting/SOAPnotifsender"
  items_url_list[7]="reporting/RESTnotifchecker"
  items_url_list[8]="reporting/RESTnotifsender"
  items_url_list[9]="reporting/dbManager/status"
  items_url_list[10]="reporting/dbMonitor/status"

  status_counter_name=${#items_name_list[*]}
  status_counter_url=${#items_url_list[*]}
  if [ $status_counter_name -ne $status_counter_url ]
  then 
    log_error "### The counter of CCDM source data:name and url is mismatch,plese check"
    ret=1
  else
    for k in $(seq 0 `expr $status_counter_name - 1 `)
    #for k in $(seq 0 1 )
    do
      format_slogan ${items_name_list[$k]}
      status=$(kubectl exec --namespace $ccdm_ns $(kubectl get pods --namespace $ccdm_ns |awk '/eric-udr-system-status-provider/{print $1}') ${url_prefix}${items_url_list[$k]} | jq . |tee -a $REPORT_FILE )
      #echo $status 
      if [ -n "$(echo $status |grep -E 'OK|STARTED')" ]
      then
        log_info "${items_name_list[$k]} ,the status is OK|STARTED " | tee -a $REPORT_FILE
      else
        log_error "${items_name_list[$k]} , the status is NOT OK." | tee -a $REPORT_FILE
        ret=1
      fi
     
    done
  
  fi
  format_slogan "Get a summary with DBmonitor information(NO Checking)."
  db_monitor_info=$(kubectl exec --namespace $ccdm_ns $(kubectl get pods --namespace $ccdm_ns |awk '/eric-udr-system-status-provider/{print $1}') ${url_prefix}"reporting/dbMonitor/summary" | jq . |tee -a $REPORT_FILE ) 
  return $ret
 

}


##########################################################################################
############################### MAIN #####################################################
##########################################################################################
#NF's namespace
ns=$1

#used to add testing information to log directory name.
test_Description=""
#wanted_param_num=1

# flag_summary 0:means the system is healthy ; 1: means unhealthy
flag_summary=0

if [  "$1" = "-h"  -o  "$1" = "--help"  ]; then 
  usage
  exit 1 
fi


if [ $# -eq 1  ] 
then 
  #Print the welcom information
  slogan="Hi, You are running: \"$0 ${ns}\" (${VERSION}) on $(hostname) ,Have fun!"
  format_slogan $slogan
elif [ $# -eq 2 ] #add the testing information to the log directory name 
then
  test_Description=$(echo $2 |sed -e 's/[ ][ ]*/-/g')
  #Print the welcom information
  slogan="Hi, You are running: \"$0 ${ns} ${test_Description}\" (${VERSION}) on $(hostname) ,Have fun!"
  format_slogan $slogan 
else
  log_error "### FAIL: the actual param num:$# is wrong, the expected is ${wanted_param_num}" 
  usage
  exit 1
fi

# define the report log file and delete the old one
current_time=$(date "+%Y%m%d%H%M%S")
REPORT_DIR="logs_${ns}_healthcheck-${test_Description}-${current_time}"
if [ ! -d $REPORT_DIR ]
then 
  mkdir $REPORT_DIR
fi

REPORT_FILE=${REPORT_DIR}"/Healthcheck-${ns}.log"


check_alarms $ns
flag_summary=$?


format_slogan "checking Kubernetes nodes state"
kubectl get nodes >> $REPORT_FILE 

nodes_state="$(kubectl get nodes | grep -vE 'Ready|NAME')"

# check if the return node list empty or not : empty is expected 
if [ ${#nodes_state} -ne 0 ]
then
  log_error "### FAIL: Kubernetes nodes State has something wrong!" |tee -a $REPORT_FILE
  flag_summary=1
else
  log_info "### INFO: All the Kubernetes nodes work fine." |tee -a $REPORT_FILE
fi



format_slogan "checking $ns Pods State"
pod_state=$(kubectl -n $ns get po -o wide | grep -vE 'Running|STATUS|Completed' | tee -a ${REPORT_FILE} )


# if pod_state is empty ,that means all pods state is normal 
if [ -z "$pod_state"  ] 
then 
  log_info "### INFO:all Pods are in Running or Completed state."|tee -a $REPORT_FILE
else 
  log_error "### FAIL:NOT all Pods are in Running or Completed state " |tee -a $REPORT_FILE
  log_error "NAME                                                          READY   STATUS             RESTARTS   AGE     IP                NODE                              NOMINATED NODE   READINESS GATES"
  log_error  $pod_state

  flag_summary=1

fi

format_slogan "checking $ns Containers State"
container_state=`kubectl -n $ns get po | grep -v Completed | awk -F"[ /]+" 'BEGIN{found=0} !/NAME/ {if ($2!=$3) { found=1; print $0}} END { if (!found) print "### All containers are up."}' |tee -a $REPORT_FILE `

if [ "$container_state" != "### All containers are up." ]
then
  log_error "### FAIL: Some of the Containers are not up." |tee -a $REPORT_FILE
  flag_summary=1
  kubectl -n $ns get po | grep -v Completed | awk -F"[ /]+" 'BEGIN{found=0} !/NAME/ {if ($2!=$3) { found=1; print $0}} END { if (!found) print "### All containers are up."}'

else
  log_info "### INFO: All containers are up."

fi


format_slogan "checking $ns Replicas State"
replica_state=`kubectl -n $ns get deploy | awk -F"[ /]+" 'BEGIN{found=0} !/NAME/ {if ($2!=$3) { found=1; print $0}} END { if (!found) print "### All desired replicas are ready"}' |tee -a $REPORT_FILE `

if [ "$replica_state" != "### All desired replicas are ready" ]
then
  log_error "### FAIL: Some of the Desired Replicas are NOT in Ready Status." |tee -a $REPORT_FILE
  flag_summary=1
  kubectl -n $ns get deploy | awk -F"[ /]+" 'BEGIN{found=0} !/NAME/ {if ($2!=$3) { found=1; print $0}} END { if (!found) print "### All desired replicas are ready"}'
else
  log_info "### INFO: All the Desired Replicas are in Ready Status."
fi


format_slogan "list Pods restart info(no Auto checking here)"

# output the pods that restart-count > 0
kubectl -n $ns get po  | head -1 | tee -a $REPORT_FILE
kubectl -n $ns get po  | grep -v NAME |awk '$4>0' | sort --reverse --key 4 --numeric
pods_restart=`kubectl -n $ns get po  | grep -v NAME |awk '$4>0' | sort --reverse --key 4 --numeric |tee -a  $REPORT_FILE `

format_slogan "list the Software Versions(no auto checking here) "
helm list -n $ns | tee -a  $REPORT_FILE

#format_slogan "checking Kubernetes Components status "
#components_state="$(kubectl get cs | grep -vE 'Healthy|NAME' | tee -a $REPORT_FILE )"


## check if the return components list empty or not : empty is expected
#if [ ${#components_state} -ne 0 ]
#then
#  log_error "### FAIL: Some of the Kubernetes components are NOT in Ready Status!" |tee -a $REPORT_FILE
#  flag_summary=1
#else
#  log_info "### INFO: All the Kubernetes components are in Ready Status." |tee -a $REPORT_FILE
#fi



format_slogan "checking Persistent Volume Claim status "


pvc_state="$(kubectl -n $ns get pvc| grep -vE 'Bound|NAME' | tee -a $REPORT_FILE )"

# check if the return data is  empty or not : empty is expected
if [ ${#pvc_state} -ne 0 ]
then
  log_error "### FAIL: Some of the Persistent Volume Claim are NOT in Bound Status!" |tee -a $REPORT_FILE
  flag_summary=1
else
  log_info "### INFO: All the Persistent Volume Claim are in Bound Status." |tee -a $REPORT_FILE
fi

# check ccdm udr system status if the current $ns contains ore equal to 'ccdm'
if [ -n "$(echo $ns |grep -i ccdm)" ]
then
  check_ccdm_udr_system_status $ns
  udr_sys_ret=$?
  # some system status is not right 
  if [ $udr_sys_ret -gt 0 ]
  then
    flag_summary=1
  fi
fi

# collect and analyze pods logs if the product is not in Healthy state.
POD_LOG_DIR="${REPORT_DIR}/podlogs-$ns"

# Summary the report 
format_slogan "                SUMMARY              "
if [ $flag_summary -gt 0 ]
then 
  log_error "### Summary: Oh,The $ns is NOT in Healthy State, Please check the logs in $REPORT_DIR for more info." |tee -a $REPORT_FILE
  if [ $COLLECT_POD_LOG_FLAG -gt 0 ]
  then 
    log_info "start collecting Pods logs for troubleshooting..."
    mkdir -p $POD_LOG_DIR
    for POD in `kubectl get pods -n $ns |grep -v NAME |awk '{print $1}'`;do echo $POD; kubectl logs $POD -n $ns  --all-containers > ${POD_LOG_DIR}/$POD.log;done
    error_logs_num=$(grep '"severity": "error"' ${POD_LOG_DIR}/*.log |wc -l)
    log_info "collect Pods logs DONE and there are $error_logs_num severity:error in pod logs."
    log_info "NOTE:You may set COLLECT_POD_LOG_FLAG=0 to disable the pod log collection FUNC."
  else
    log_info "NOTE:pod logs collection FUNC is disabled ,you may set COLLECT_POD_LOG_FLAG=1 to enable it."
  fi

else
  log_info "### Summary: Congratulations!, The $ns is in Healthy State." |tee -a $REPORT_FILE

fi

echo; echo 

# save the detailed information for troubleshooting
Detailed_LOG=${REPORT_DIR}/detailed-info-${ns}.log
echo "The detailed information of $ns" > ${Detailed_LOG}
kubectl get all -n $ns >> ${Detailed_LOG}

