import sys
import json
from urllib.request import urlopen
from urllib.error import URLError
from urllib.error import HTTPError
import datetime
import os
import errno
import xml.etree.ElementTree as ElementTree

JCENTER = "jcenter"
JCENTER_URL = "http://jcenter.bintray.com"

MVN_CENTRAL = "mvn-central"

SKIP_KEYWORDS = ['-alpha', '-prealpha', '-beta', '-rc', '-dev', '-snapshot']

MISSING_LIB = []

def unix2Date(unixTime):
    unixTime = int(str(unixTime)[:-3])
    return datetime.datetime.fromtimestamp(unixTime).strftime('%d.%m.%Y')


def retry_if_error(exception):
    raise exception
    ret = isinstance(exception, URLError) or isinstance(exception, HTTPError)
    return ret


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def write_library_description(xml_name, repo, groupid, artefactid, version, category="", date="", comment=""):
    # make_sure_path_exists(os.path.dirname(xml_name))

    # write lib description in xml format
    with open(xml_name, "w") as desc:
        desc.write("<?xml version=\"1.0\"?>\n")
        desc.write("<library>\n")
        desc.write("    <name>{}:{}:{}</name>\n".format(groupid, artefactid, version))
        desc.write("\n")
        desc.write("    <category>{}</category>\n".format(category))
        desc.write("\n")
        desc.write("    <groupId>{}</groupId>\n".format(groupid))
        desc.write("\n")
        desc.write("    <repo>{}</repo>\n".format(repo))
        desc.write("\n")
        desc.write("    <artefactId>{}</artefactId>\n".format(artefactid))
        desc.write("\n")
        desc.write("    <version>{}</version>\n".format(version))
        desc.write("\n")
        desc.write("    <releasedate>{}</releasedate>\n".format(date))
        desc.write("\n")
        desc.write("    <comment>{}</comment>\n".format(comment))
        desc.write("</library>\n")


def downloadLibFile(targetDir, repo, groupid, artefactid, version, filetype):
    # assemble download URL
    artefactid_r = artefactid.replace(".","/")
    groupid_r = groupid.replace(".","/")
    if repo == MVN_CENTRAL:
        repoURL = "http://search.maven.org/remotecontent?filepath="
    else:
        repoURL = repo

    if filetype in ['jar', 'aar']:
        fileName = artefactid_r + "-" + version + "." + filetype
        URL = repoURL + groupid_r + "/" + artefactid_r + "/" + version + "/" + fileName
        targetFile = os.path.join(targetDir, f"{groupid}_{artefactid}_{version}.{filetype}")
        try:
            libFile = urlopen(URL)
            with open(targetFile,'wb') as output:
                output.write(libFile.read())
            xml_name = os.path.join(targetDir, f"{groupid}_{artefactid}_{version}.xml")
            write_library_description(xml_name, repo, groupid, artefactid, version)
        except Exception as e:
            print(URL)
            raise e
    else:
        print("\t\t[*] change file type")
        for filetype in ['jar','aar']:
            fileName = artefactid_r + "-" + version + "." + filetype
            URL = repoURL + groupid_r + "/" + artefactid_r + "/" + version + "/" + fileName
            targetFile = os.path.join(targetDir, f"{groupid}_{artefactid}_{version}.{filetype}")
            try:
                libFile = urlopen(URL)
                with open(targetFile,'wb') as output:
                    output.write(libFile.read())
                xml_name = os.path.join(targetDir, f"{groupid}_{artefactid}_{version}.xml")
                write_library_description(xml_name, repo, groupid, artefactid, version)
                return
            except HTTPError as e:
                print(f"\t\t[*] {filetype} invalid, change")
            except Exception as e:
                print(URL)
                raise e
        raise Exception("INVALID jar or aar")
    # except HTTPError as e:
    #     if filetype != 'aar':
    #         print('    !! HTTP Error while retrieving ' + filetype + ' file:  ' + str(e.code))
    #     raise e
    #     return 1
    # except URLError as e:
    #     print('    !! URL Error while retrieving ' + filetype + ' file: ' + str(e.reason))
    #     return 1
    # except Exception as excp:
    #     print('    !! Download failed: ' + str(excp))
    #     return 1



## library updating routine for mvn central
def updateLibraryMvnCentral(groupId, artefactId, localRepoDir, errorFile, skipAlphaBeta=True):
    libName = f"{groupId}_{artefactId}"
    print(f"[*] check library {groupId}:{artefactId} @ mvn-central")

    # Assemble mvn central search URL and retrieve meta data
    try:
        mvnSearchURL = "http://search.maven.org/solrsearch/select?q=g:%22" + groupId + "%22+AND+a:%22" + artefactId + "%22&rows=100&core=gav"
        response = urlopen(mvnSearchURL)
        data = json.loads(response.read())
    except Exception as e:
        print(mvnSearchURL)
        raise e
    # except URLError as e:
    #     raise e
    #     print('URLError = ' + str(e.reason))
    #     return
    # except Exception as excp:
    #     print('Could not retrieve meta data for ' + libName + '  [SKIP]  (' + str(excp) + ')')
    #     return

    # DEBUG: pretty print json
    # print(json.dumps(data, indent=4, sort_keys=True))
    # print()

    numberOfVersions = data["response"]["numFound"]
    print("\t- retrieved meta data for " + str(numberOfVersions) + " versions:")

    numberOfUpdates = 0
    if numberOfVersions > 0:
        for version in data["response"]["docs"]:
            if skipAlphaBeta and any(x in version["v"].lower() for x in SKIP_KEYWORDS):
                continue;
            # skip lib version if already existing
            libtype = version['p']
            if not os.path.isfile(os.path.join(localRepoDir, f"{libName}_{version['v']}.xml")):
            # if not os.path.isfile(baseDirName + "/" + version["v"] + "/" + LIB_DESCRIPTOR_FILE_NAME):
                numberOfUpdates += 1
                date = unix2Date(version["timestamp"])

                print(f"       - update version: {version['v']}   type: {libtype}  date: {date}  target-dir: {localRepoDir}")
                try:
                    downloadLibFile(localRepoDir, MVN_CENTRAL, groupId, artefactId, version["v"], libtype)
                except Exception as e:
                    # print(json.dumps(data, indent=4, sort_keys=True))
                    # raise e
                    print("\t[!]ERROR, download failed, logged")
                    with open(errorFile, 'a') as fw:
                        fw.write(f"{libName}:{version['v']}@mvn-central\n")
                    # raise e


    if numberOfUpdates == 0:
        print("      -> all versions up-to-date")




## library updating routine for jcenter + custom mvn repos
def updateLibrary(repoURL, groupId, artefactId, localRepoDir, errorFile, skipAlphaBeta=True):
    libName = f"{groupId}_{artefactId}"
    print(f"[*] check library {groupId}:{artefactId} @ {repoURL}")

    # Assemble base URL and retrieve meta data
    try:
        if repoURL == "jcenter":
            repoURL = JCENTER_URL

        if not repoURL.endswith("/"):
            repoURL = repoURL + "/"

        metaURL = repoURL + groupId.replace(".","/") + "/" + artefactId.replace(".","/") + "/maven-metadata.xml"

        response = urlopen(metaURL)
        data = response.read()
        response.close()
    except Exception as e:
        print(metaURL)
        raise e
    # except URLError as e:
    #     print('URLError = ' + str(e.reason))
    #     return
    # except Exception as excp:
    #     print('Could not retrieve meta data for ' + libName + '  [SKIP]  (' + str(excp) + ')')
    #     return

    # retrieve available versions
    versions = []
    root = ElementTree.fromstring(data)
    for vg in root.find('versioning'):
        for v in vg.iter('version'):
            if not skipAlphaBeta or (skipAlphaBeta and not any(x in v.text.lower() for x in SKIP_KEYWORDS)):
                versions.append(v.text)

    numberOfVersions = len(versions)
    print("    - retrieved meta data for " + str(numberOfVersions) + " versions:")

    numberOfUpdates = 0
    if numberOfVersions > 0:
        for version in versions:
            if skipAlphaBeta and any(x in version.lower() for x in SKIP_KEYWORDS):
                continue;
            # skip lib version if already existing
            libtype = 'Unknown'
            if not os.path.isfile(os.path.join(localRepoDir, f"{libName}_{version}.xml")):
            # if not os.path.isfile(baseDirName + "/" + version["v"] + "/" + LIB_DESCRIPTOR_FILE_NAME):
                numberOfUpdates += 1
                date = 'N/A'

                print(f"       - update version: {version}   type: {libtype}  date: {date}  target-dir: {localRepoDir}")
                try:
                    downloadLibFile(localRepoDir, repoURL, groupId, artefactId, version, libtype)
                except Exception as e:
                    # print(json.dumps(data, indent=4, sort_keys=True))
                    print("\t[!]ERROR, download failed, logged")
                    with open(errorFile, 'a') as fw:
                        fw.write(f"{libName}:{version}@{repoURL}\n")


    if numberOfUpdates == 0:
        print("      -> all versions up-to-date")

def main():
    skipAlphaBeta = True                    # skip alpha and beta versions

    # Requires two arguments (path to json file with library descriptions)
    args = len(sys.argv)
    if args != 4:
        print("Usage: " + sys.argv[0] + "  <libraries.json>" + "  <libraries directory>" + "  <error.txt>")
        sys.exit(1)
    else:
        inputFile = sys.argv[1]
        localRepoDir = sys.argv[2]
        errorFile = sys.argv[3]
        print("- Load library info from " + sys.argv[1])

    print("- Store libs to " + localRepoDir)
    make_sure_path_exists(localRepoDir)
    # load library definitions
    with open(inputFile) as ifile:
        data = json.load(ifile)

    # update each lib
    print("- Update libraries" + (" (skip alpha/beta versions)" if skipAlphaBeta else "") + ":")
    for lib in data["libraries"]:
        if 'repo' not in lib:
            print("[WARN] Skip library: " + lib["name"] + "  (No repo defined!)")
            continue

        elif lib['repo'] == MVN_CENTRAL:
            updateLibraryMvnCentral(lib["groupid"], lib["artefactid"], localRepoDir, errorFile, skipAlphaBeta)

        else:  # jcenter or custom mvn repo URL
            updateLibrary(lib['repo'], lib["groupid"], lib["artefactid"], localRepoDir, errorFile, skipAlphaBeta)
    return


if __name__ == "__main__":
    main()