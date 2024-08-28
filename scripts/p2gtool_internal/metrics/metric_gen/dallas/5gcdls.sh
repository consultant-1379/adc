#!/bin/bash

# 2015-09-23: ervmapa
# adding variable -r for resetting diff values. Example  -r "17:43:00"

################################################################################
# lts_pmshow for combined node under test
###############################################################################
pmshow_cgw () {
/lab/testtools/dallas/rhel764/preRelease/3R150A16/bin/lts_pmshow ${file}  -c 'System - Total signaling - Rate;Total signaling KPI - Attempted;Total signaling KPI - Failed;NR - Active PDU Session Number - Value;LTT Payload - Gi UL bytes - Rate;LTT Payload - Gn/Iuu DL bytes - Rate;LTT Payload - Uplink Packets dropped \(E2E\) - Value;LTT Payload - Downlink Packets dropped \(E2E\) - Value;LTT Payload - Gi DL packets - Value;LTT Payload - Gn/Iuu UL packets - Value;LTT Payload - Gi UL packets - Rate;LTT Payload - Gn/Iuu DL packets - Rate;NR - Inactive PDU Session Number - Value;NR - RM-REGISTERED UE Number - Value;NR - RM-REGISTERED CM-IDLE UE Number - Value;LTE - Attached CM-CONNECTED UE - Value;LTE - Attached CM-IDLE UE - Value;LTE - Attach Request\(IMSI\) - Rate;LTE - Attach Request\(IMSI\) - RTT;LTE - Attach Request\(IMSI\) - Failed;LTE - Attach Request\(GUTI\) - Rate;LTE - Attach Request\(GUTI\) - RTT;LTE - Attach Request\(GUTI\) - Failed;LTE - Attach Reject - Rate;LTE - Detach Request - Rate;LTE - Detach Request - RTT;LTE - Detach Request - Failed;LTE - Tracking Area Update Request - Rate;LTE - Tracking Area Update Request - RTT;LTE - Tracking Area Update Request - Failed;LTE - Tracking Area Update Request\(After Handover\) - Rate;LTE - Tracking Area Update Request\(After Handover\) - RTT;LTE - Tracking Area Update Request\(After Handover\) - Failed;LTE - Tracking Area Update Request\(After Handover Failure\) - Rate;LTE - Tracking Area Update Request\(After Handover Failure\) - RTT;LTE - Tracking Area Update Request\(After Handover Failure\) - Failed;LTE - Handover Require - Rate;LTE - Handover Require - RTT;LTE - Handover Require - Failed;LTE - Path Switch Request - Rate;LTE - Path Switch Request - RTT;LTE - Path Switch Request - Failed;LTE - Service Request - Rate;LTE - Service Request - RTT;LTE - Service Request - Failed;LTE - Service Reject - Rate;LTE - Service Release - Rate;LTE - Service Release - RTT;LTE - Service Release - Failed;LTE - PDN Connectivity Request - Rate;LTE - PDN Connectivity Request - RTT;LTE - PDN Connectivity Request - Failed;LTE - Disconnect PDN Request - Rate;LTE - Disconnect PDN Request - RTT;LTE - Disconnect PDN Request - Failed;NR - Initial Registration Request \(SUCI\) - Rate;NR - Initial Registration Request \(SUCI\) - RTT;NR - Initial Registration Request \(SUCI\) - Failed;NR - Initial Registration Request \(GUTI\) - Rate;NR - Initial Registration Request \(GUTI\) - RTT;NR - Initial Registration Request \(GUTI\) - Failed;NR - Mobility Registration Request - Rate;NR - Mobility Registration Request - RTT;NR - Mobility Registration Request - Failed;NR - Service Request \(UE Init\) - Rate;NR - Service Request \(UE Init\) - RTT;NR - Service Request \(UE Init\) - Failed;NR - Service Request \(NW Init\) - Rate;NR - Service Request \(NW Init\) - RTT;NR - Service Request \(NW Init\) - Failed;NR - PDU Session Establishment Request - Rate;NR - PDU Session Establishment Request - RTT;NR - PDU Session Establishment Request - Failed;NR - PDU Session Release Request - Rate;NR - PDU Session Release Request - RTT;NR - PDU Session Release Request - Failed;NR - PDU Session Release Cmd\/Cmpt - Rate;NR - PDU Session Release Cmd\/Cmpt - RTT;NR - PDU Session Release Cmd\/Cmpt - Failed;NR - Path Switch Request - Rate;NR - Path Switch Request - RTT;NR - Path Switch Request - Failed;NR - Handover Required - Rate;NR - Handover Required - RTT;NR - Handover Required - Failed;System - Signallings rtt hit the range 10 - Value;Signallings rtt hit the range 30 - Value;Signallings rtt hit the range 50 - Value;Signallings rtt hit the range 100 - Value;Signallings rtt hit the range 150 - Value;Signallings rtt hit the range 300 - Value;Signallings rtt hit the range 800 - Value;Signallings rtt hit the range 1000 - Value;Signallings rtt hit the range 2000 - Value;Signallings rtt hit the range 5000 - Value;Signallings rtt hit the range 10000 - Value;Signallings rtt hit the range 20000 - Value;Signallings rtt hit the range 50000 - Value;Total signaling KPI - Resendings;LTT Payload - Error Indication sent - Value'  | awk -v showdelta=${delta} -v showverbose=${verbose} -v offset_ul=0 -v offset_dl=0  -v pud=0 -v pdd=0 -v ref_time=${ref_time} '{
    date=$1
    if (date != "Time")
    {
      if (date ~ /^20[0-9][0-9]-/)
      {
        time=$2
        tsr=$3
        tsa=$4
        tsf=$5
        tap=$6
        pgubr=$7*8/1000/1000/1000
        pgdbr=$8*8/1000/1000/1000
        pdd=$9-pud
        pddd=$10-pdd
        pud=$9
        pdd=$10
        puv=$12
        pdv=$11
        ppsdl=$14
        ppsul=$13
        idlPdu=$15
        RegUe=$16
        idleUe=$17
        lteUE=$18+$19
        if (tsa==0) tsa=0.00001
        if (showdelta ~ /true/)
         {
          format="%-10s  %-8s  %11i  %11i  %11i  %14i  %14i  %14i  %14i  %14i %14i %11i   %11i  %10i  %10i %13.4f %5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%4.2f	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i	%5.1f	%4.2f	%8i %5i %5i %5i %5i %5i %5i %5i %5i %5i %5i %5i %5i %5i %8i %11i\n"
          printf format, date, time, tsr, tsa, tsf, pud, pdd, puv, pdv, ppsul,  ppsdl, pgubr, pgdbr, RegUe, lteUE, tsf, $20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$40,$41,$42,$43,$44,$45,$46,$47,$48,$49,$50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$60,$61,$62,$63,$64,$65,$66,$67,$68,$69,$70,$71,$72,$73,$74,$75,$76,$77,$78,$79,$80,$81,$82,$83,$84,$85,$86,$87,$88,$89,$90,$91,$92,$93,$94,$95,$96,$97,$98,$99,$100,$101,$102
        } else {
          format="%-10s  %-8s  %10i  %13.1f  %10i  %13.1f\n"
          printf format, date, time, uldiff, 1000000*(uldiff)/(gnul+0.001), dldiff, 1000000*(dldiff)/(gidl+0.001)
        }
      }
    }
  }'

}

################################################################################
# MAIN
################################################################################

# Parse command line
file=""
delta="true"
verbose="false"
loop="true"
ref_time="false"
interval=15

while getopts ":r:f:dvht" opts
do
  case "$opts" in
    "f") file="-f $OPTARG/dallas_pm.log";;
    "d") delta="true";;
    "v") verbose="true";;
    "t") loop="true";;
    "r") ref_time="$OPTARG";;
    "i") interval="$OPTARG";;
    "h") usage ;;
    "?") ${ECHO}
         ${ECHO} "ERROR: Unknown option '$OPTARG'!"
         ${ECHO}
         exit 1;;
    ":") ${ECHO}
         ${ECHO} "ERROR: Missing value for option '$OPTARG'!"
         ${ECHO}
         exit 1;;
  esac
done


#total signaling
st_runtime()
{
  if [ ! -e /var/log/dallas_msg.log ];then
    echo 0
    return
  fi
  this_year=$(date +%Y)
  time_log=`grep lts_run_tm /var/log/dallas_msg.log|tail -n 1|awk -v this_year=$this_year {'print this_year"-"$2,$3'}`
  trans_log=`date -d "$time_log" +"%s"`
  time_now=`date +%Y-%m-%d' '%H:%M:%S.%N | cut -b 1-23`
  trans_now=`date -d "$time_now" +"%s"`
  cost=`echo $trans_now-$trans_log|bc`
  time_cost=`echo "scale=1; $cost/3600"|bc`
  if [[ "$time_log" != "" ]];then
    echo $time_cost
  else
    echo "0"
  fi
}


metric_name=("stability_lead_time" "total_signal_rate" "total_signaling_attempt" "total_signaling_fail"  "payload_uplink_drop" "payload_downlink_drop" "payload_uplink_value" "payload_downlink_value" "payload_uplink_rate" "payload_downlink_rate" "payload_ul_throughput" "payload_dl_throughput" "lte_attach_imsi_rate" "lte_attach_imsi_rtt" "lte_attach_imsi_failed" "lte_attach_guti_rate" "lte_attach_guti_rtt" "lte_attach_guti_failed" "lte_attach_reject_rate" "lte_detach_rate" "lte_detach_rtt" "lte_detach_failed" "lte_track_rate" "lte_track_rtt" "lte_track_failed" "lte_track_ho_rate" "lte_track_ho_rtt" "lte_track_ho_failed" "lte_track_ho_fa_rate" "lte_track_ho_fa_rtt" "lte_track_ho_fa_failed" "lte_ho_rate" "lte_ho_rtt" "lte_ho_failed" "lte_xn_rate" "lte_xn_rtt" "lte_xn_failed" "lte_service_rate" "lte_service_rtt" "lte_service_failed" "lte_service_reject_rate" "lte_service_release_rate" "lte_service_release_rtt" "lte_service_release_failed" "lte_pdn_rate" "lte_pdn_rtt" "lte_pdn_failed" "lte_dis_pdn_rate" "lte_dis_pdn_rtt" "lte_dis_pdn_failed" "nr_reg_suci_rate" "nr_reg_suci_rtt" "nr_reg_suci_failed" "nr_reg_guti_rate" "nr_reg_guti_rtt" "nr_reg_guti_failed" "nr_mobi_reg_rate"  "nr_mobi_reg_rtt" "nr_mobi_reg_failed" "nr_service_ue_rate"  "nr_service_ue_rtt" "nr_service_ue_failed" "nr_service_nw_rate"  "nr_service_nw_rtt" "nr_service_nw_failed" "nr_pdu_est_rate"  "nr_pdu_est_rtt" "nr_pdu_est_failed" "nr_pdu_rel_rate"  "nr_pdu_rel_rtt" "nr_pdu_rel_failed" "nr_pdu_rel_cmd_rate"  "nr_pdu_rel_cmd_rtt" "nr_pdu_rel_cmd_failed" "nr_xn_rate" "nr_xn_rtt" "nr_xn_failed" "nr_n2_ho_rate"  "nr_n2_ho_rtt" "nr_n2_ho_failed" "signaling_rtt_10" "signaling_rtt_30" "signaling_rtt_50" "signaling_rtt_100" "signaling_rtt_150" "signaling_rtt_300" "signaling_rtt_800" "signaling_rtt_1000" "signaling_rtt_2000" "signaling_rtt_5000" "signaling_rtt_10000" "signaling_rtt_20000" "signaling_rtt_50000" "total_signaling_resending" "total_error_indication")
metric_value=($(st_runtime) $(pmshow_cgw 2>/dev/null | awk 'END{print $0}' | awk '{print $3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$40,$41,$42,$43,$44,$45,$46,$47,$48,$49,$50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$60,$61,$62,$63,$64,$65,$66,$67,$68,$69,$70,$71,$72,$73,$74,$75,$76,$77,$78,$79,$80,$81,$82,$83,$84,$85,$86,$87,$88,$89,$90,$91,$92,$93,$94,$95,$96,$97,$98,$99}'))

i=0
for m in ${metric_name[@]}
do
    echo $m=${metric_value[$i]:-0}
    let i++
done
