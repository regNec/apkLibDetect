import os
import sys
import json
import glob
import errno
from itertools import repeat
import subprocess
import multiprocessing



# LibScout config
LIBSCOUT_ROOT = os.path.dirname(os.path.realpath(__file__))
LIBSCOUT = os.path.join(LIBSCOUT_ROOT, 'build', 'libs', 'LibScout.jar')
ANDROID_SDK = os.path.join(LIBSCOUT_ROOT, 'android-sdk', 'android-28.jar')
VUL_JSON = os.path.join(LIBSCOUT_ROOT, 'vuls', 'vuls.json')

def usage():
    print(sys.argv[0])
    print(f"Usage: {sys.argv[0]} <apk_file_or_directory> <output_directory> <summary_report.json>")


def search_vul(lib_detect_json: str, vuls: dict):
    with open(lib_detect_json, 'r') as fr:
        s = json.load(fr)
        num = len(s['lib_matches'])
    result ={}
    for i in range(num):
        lst = s['lib_matches'][i]['libName'].split('_')
        groupid = lst[0]
        artifactid = lst[1]
        version = s['lib_matches'][i]['libVersion']
        package = str(groupid + ':' + artifactid + '@' + version)
        try:
            result[package] = vuls[package]
        except KeyError:
            result[package] = 'No vulnerability'
    return result
    

def run_tool_chain(apk_file: str, output: str, vuls: dict):
    apk_file_name = os.path.splitext(os.path.basename(apk_file))[0]
    lib_detct_json_name = apk_file_name + '.json'
    lib_detct_out = os.path.join(output, 'lib')
    lib_detct_json = os.path.join(lib_detct_out, lib_detct_json_name)
    if not os.path.exists(lib_detct_json):
        run_libscout_cmd = f"java -jar {LIBSCOUT} -o match -p profiles/lib -a {ANDROID_SDK} -j \"{lib_detct_out}\" \"{apk_file}\""
        try:
            out_bytes = subprocess.check_output(run_libscout_cmd, shell=True)
        except subprocess.CalledProcessError as e:
            out_bytes = e.output        # Output generated before error
            code = e.returncode         # Return code
            print(f"[*] Run LibScout Error, Code: {code}, apk: {apk_file}")
        print(f"[*] Library detection for {apk_file} finished, Lib Info stored in {output}/")
    else:
        print(f"[*] Library detection result found for {apk_file}, skip detection")
    
    if not os.path.exists(lib_detct_json):
        print(f"[!] Error in LibScout library detection, exit")
        return {apk_file: "Lib Detection Error"}
    
    print(f"[*] Search vulerabilities in {apk_file}")
    vul_result = search_vul(lib_detct_json, vuls)
    res_json = os.path.join(output, 'vul', apk_file_name + '.json')
    with open(res_json, 'w') as fj:
        json.dump(vul_result, fj)
    print(f"[*] Vulerabilities info stored in {res_json}")
    return {apk_file: vul_result}


def report_vul_app(vul_report):
    report = {}
    for apk_file, app_vul_info in vul_report.items():
        apk_vuls = []
        if app_vul_info == "Lib Detection Error":
            report.setdefault(os.path.basename(apk_file), app_vul_info)
        else:
            for lib_info, lib_vul in app_vul_info.items():
                if lib_vul != "No vulnerability":
                    apk_vuls.append({lib_info:lib_vul})
                    print(f"[*] Got Vulnerability: {apk_file} -> {lib_info}")
            report.setdefault(os.path.basename(apk_file), apk_vuls)
        # apk_vuls = []
    return report

def main():
    if len(sys.argv) != 4:
        usage()
        return
    else:
        apk = sys.argv[1]
        output = sys.argv[2]
        summary_report_path = sys.argv[3]
    if not os.path.exists(apk):
        usage()
        print("Invalid apk path or directory")
        return

    if not os.path.exists(VUL_JSON):
        print(f"Missing vulnerability json file {VUL_JSON}")
        return
    else:
        with open(VUL_JSON, 'r') as fr:
            vuls = json.load(fr)

    # make sure output directory exist
    try:
        os.makedirs(os.path.join(output, 'lib'))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise exception
    try:
        os.makedirs(os.path.join(output, 'vul'))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise exception
    
    for f in [LIBSCOUT, ANDROID_SDK]:
        if not os.path.isfile(f):
            print(f"Invalid {f}")
            return
    
    vul_report = {}
    res = []
    if os.path.isfile(apk):
        res.append(run_tool_chain(apk, output))
    else:
        with multiprocessing.Pool(processes=(multiprocessing.cpu_count() - 1)) as pool:
            res = pool.starmap(run_tool_chain, zip(glob.glob(f"{apk}/*.apk"), repeat(output), repeat(vuls)))
    for res_d in res:
        vul_report.update(res_d)
    
    report_summary = report_vul_app(vul_report)
    with open(summary_report_path, 'w') as fw:
        json.dump(report_summary, fw, indent=4, sort_keys=True)
    print(f"[*] Summary dumped to {summary_report_path}")
    return

def test():
    print(glob.glob("profile.sh/*.apk"))

if __name__ == '__main__':
    # test()
    main()