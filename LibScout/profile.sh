#! /bin/bash
LIBSCOUT_ROOT="."
LIBSCOUT="${LIBSCOUT_ROOT}/build/libs/LibScout.jar"
ANDROID_SDK="${LIBSCOUT_ROOT}/android-sdk/android-28.jar"
LIB_DIR="${LIBSCOUT_ROOT}/library"
total=`find "${LIB_DIR}" -name "*.[aj]ar" | wc -l`
count=0
start=`date +%s`
while read lib_file
do
    name="${lib_file%.*}"
    xml_file="${name}.xml"
    if [ -f "${xml_file}" ]; then
        echo -e "[*] profile ${lib_file}"
        java -jar "${LIBSCOUT}" -o profile -a "${ANDROID_SDK}" -x "${xml_file}" "${lib_file}" > /dev/null
    else
        echo -e "Missng ${xml_file}"
    fi
    count=$[count + 1]
    end=`date +%s`
    echo "${count} profiled ($[${end} - ${start}] secs) - total${total} "
done < <(find "${LIB_DIR}" -name "*.[aj]ar")