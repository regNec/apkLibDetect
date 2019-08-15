# apkLibDetect

工具链由两部分组成：

- 前端为LibScout - https://github.com/reddr/LibScout
- 后端为从snyk采集的数据库 - https://snyk.io/vuln

## Run

```bash
Usage: 
	python3 run.py <apk_file_or_directory> <output_directory> <summary_report.json>
```

#### Output Structure

```python
<output_directory>
├── lib # LibScout Library detection result, <apk_name>.json
└── vul # Apk Vulnerability result, <apk_name>.json
```

**<summary_report.json>** 为所有apk漏洞报告的摘要，提取了存在漏洞的包及漏洞信息，过滤其他没有查询到漏洞的包

**NOTE:**输入为apk目录时，默认使用 ( CPU core - 1 ) 个进程。输入为单个apk时，使用单个进程。

## Structure

```python
.
├── LibScout # Revised LibScout directory
│   ├── LICENSE # LibScout Lisense
│   ├── README.md # LibScout README
│   ├── android-sdk # LibScout requires an android SDK
│   ├── assets
│   ├── build
│   ├── build.gradle
│   ├── config
│   ├── data
│   ├── gradle
│   ├── gradlew
│   ├── gradlew.bat
│   ├── lib
│   ├── library # Original Library files (jar or aar), and description file (xml)
│   ├── profile.sh # generate profiles for libraries
│   ├── profiles # generated profiles
│   ├── run.py # RUN THE TOOLCHAIN
│   ├── scripts # scripts to collect library
│   ├── src # LibScout Source Code
│   └── vuls # vulnerability database
└── README.md
└── vulnerability # generate vulnerability database
    ├── example
    └── vuls.py # generation script
```

## Usage

### Requrements:

- Python3 (No third party package needed)
- Java 1.8 or higher and can be build with Gradle (for LibScout)

### 添加library

- 仅支持.jar或.aar
- 将库文件和库描述文件放在`./LibScout/library`下
- 运行`java -jar ./LibScout/build/libs/LibScout.jar -o profile -a ./LibScout/android-sdk/android-28.jar -x  -x "${xml_file}" "${lib_file}"`
- 加入多个Library可使用profile.sh

#### Library File Name Format

`groupID_artefactID_version.jar or aar`

Example: android.arch.core_common_1.0.0.jar

#### Library Description XML File format

文件名应和库文件名相同

Example: android.arch.core_common_1.0.0.xml

```xml
<?xml version="1.0"?>
<library>
    <name>android.arch.core_common</name>

    <category>lib</category>

    <groupId>android.arch.core</groupId>

    <repo>https://dl.google.com/dl/android/maven2/</repo>

    <artefactId>common</artefactId>

    <version>1.0.0</version>

    <releasedate></releasedate>

    <comment></comment>
</library>
```

### 构建漏洞数据库

#### 环境依赖

- Ubuntu 18.04.3 LTS

- python3

- gradle

  `sudo apt-get install gradle`

- maven版本 > 2

  `sudo apt install maven`

- snyk CLI

  `npm install -g snyk`

#### 编写第三方库依赖文件

样例：**example/build.gradle**

添加第三方库依赖：

```
dependencies {
    provided 'groupid:artifactid:version'
}
```

增加新的仓库：

```gra
maven {
    url "仓库地址"
}
```

无法增加仓库来解决的情况下，可能需要增加（以下为样例）

```
dependencies {
    compile 'com.koushikdutta.ion:ion:1.+'
}
```

**注意**

- 文件名必须为**build.gradle**

- 相同的`groupie:artifactid`对应的不同的版本号不能写在同一个**build.gradle**文件中，否则默认为高版本的情况，忽略所有的低版本，例如：

  ```
  provided 'com.amazonaws:aws-android-sdk-mobileanalytics:2.1.10'
  provided 'com.amazonaws:aws-android-sdk-mobileanalytics:2.1.3'
  ```

- 具体情况需要根据后续运行snyk的报错来进行相应的修改

#### 查询build.gradle中第三方库的漏洞

在存放build.gradle的目录下运行`snyk test --json > relative_path_to_ouputjsonfile`

输出格式为json

此过程可能会出现很多报错，依据报错作出相应的修改，这里说明一下无法解析包（example: Could not resolve groupid:artifactid:version）的报错

- 可以通过增加新的仓库或增加`compile`（详见上一模块所述）

- 可以手动安装包

  - 通过pom文件和aar文件

    下载相应包的pom文件和aar文件，运行`mvn install:install-file -Dfile=path_to_aar_file -DpomFile=path_to_pom_file`

  - 通过jar文件

    下载相应包的jar文件，运行`mvn install:install-file -Dfile=path_to_jar_file -DgroupId=groupid -DartifactId=artifactid -Dversion=version -Dpackaging=jar`

生成的漏洞报告可见如下示例（示例中为一个漏洞信息），详细信息见**example/snyk-output-file.json**：

```json
{
      "CVSSv3": "CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "alternativeIds": [],
      "creationTime": "2018-07-10T07:33:37.781000Z",
      "credit": [
        "Unknown"
      ],
      "cvssScore": 9.8,
      "description": "## Overview\r\n[org.bouncycastle:bcprov-jdk15on](https://github.com/bcgit/bc-java) is a Java implementation of cryptographic algorithms.\r\n\r\nAffected versions of this package are vulnerable to Unexpected Code Execution via the `XMSS/XMSS^MT` private key deserialization. A handcrafted private key could include references to unexpected classes which would be picked up from the class path for the executing application.\r\n\r\n## Remediation\r\nUpgrade `org.bouncycastle:bcprov-jdk15on` to version 1.60 or higher.\r\n\r\n## References\r\n- [GitHub Commit](https://github.com/bcgit/bc-java/commit/cd98322b171b15b3f88c5ec871175147893c31e6#diff-148a6c098af0199192d6aede960f45dc)",
      "disclosureTime": "2018-03-03T07:33:37Z",
      "fixedIn": [
        "1.60"
      ],
      "functions": [
        {
          "functionId": {
            "className": "XMSSUtil",
            "filePath": "org/bouncycastle/pqc/crypto/xmss/XMSSUtil.java",
            "functionName": "isNewAuthenticationPathNeeded"
          },
          "version": [
            "[,1.60)"
          ]
        }
      ],
      "functions_new": [
        {
          "functionId": {
            "className": "org.bouncycastle.pqc.crypto.xmss.XMSSUtil",
            "functionName": "isNewAuthenticationPathNeeded"
          },
          "version": [
            "[,1.60)"
          ]
        }
      ],
      "id": "SNYK-JAVA-ORGBOUNCYCASTLE-32412",
      "identifiers": {
        "CVE": [
          "CVE-2018-1000613"
        ],
        "CWE": [
          "CWE-470"
        ]
      },
      "language": "java",
      "mavenModuleName": {
        "artifactId": "bcprov-jdk15on",
        "groupId": "org.bouncycastle"
      },
      "modificationTime": "2018-11-22T10:10:10.072114Z",
      "moduleName": "org.bouncycastle:bcprov-jdk15on",
      "packageManager": "maven",
      "packageName": "org.bouncycastle:bcprov-jdk15on",
      "patches": [],
      "publicationTime": "2018-07-19T14:10:09Z",
      "references": [
        {
          "title": "GitHub Commit",
          "url": "https://github.com/bcgit/bc-java/commit/cd98322b171b15b3f88c5ec871175147893c31e6%23diff-148a6c098af0199192d6aede960f45dc"
        }
      ],
      "semver": {
        "vulnerable": [
          "[,1.60)"
        ]
      },
      "severity": "high",
      "title": "Unexpected Code Execution",
      "from": [
        "gradle@0.0.0",
        "com.android.tools:sdk-common@26.0.0-alpha2",
        "org.bouncycastle:bcpkix-jdk15on@1.56",
        "org.bouncycastle:bcprov-jdk15on@1.56"
      ],
      "upgradePath": [],
      "isUpgradable": false,
      "isPatchable": false,
      "name": "org.bouncycastle:bcprov-jdk15on",
      "version": "1.56"
}
```

#### 生成漏洞数据库

`Usage: python3 vuls.py <path_to_snykoutput_dir>`

在当前目录下的**vuls**目录中生成**vuls.json**，示例：

key：包名（groupid:artifactid@version）

value：此包对应的漏洞信息（可能会有多个漏洞信息，如下有两个）

```json
"com.mapbox.mapboxsdk:mapbox-android-sdk@6.6.4": [
        {
            "identifiers": {
                "CVE": [
                    "CVE-2018-1000850"
                ],
                "CWE": [
                    "CWE-22"
                ]
            },
            "references": [
                {
                    "title": "GitHub Commit",
                    "url": "https://github.com/square/retrofit/commit/b9a7f6ad72073ddd40254c0058710e87a073047d"
                },
                {
                    "title": "I Hack To Protect Blog",
                    "url": "https://ihacktoprotect.com/post/retrofit-path-traversal/"
                }
            ],
            "title": "Directory Traversal",
            "from": [
                "snyk@0.0.0",
                "com.mapbox.mapboxsdk:mapbox-android-sdk@6.6.4",
                "com.mapbox.mapboxsdk:mapbox-sdk-turf@3.4.1",
                "com.mapbox.mapboxsdk:mapbox-sdk-core@3.4.1",
                "com.squareup.retrofit2:retrofit@2.4.0"
            ]
        },
        {
            "identifiers": {
                "CVE": [
                    "CVE-2018-1000850"
                ],
                "CWE": [
                    "CWE-22"
                ]
            },
            "references": [
                {
                    "title": "GitHub Commit",
                    "url": "https://github.com/square/retrofit/commit/b9a7f6ad72073ddd40254c0058710e87a073047d"
                },
                {
                    "title": "I Hack To Protect Blog",
                    "url": "https://ihacktoprotect.com/post/retrofit-path-traversal/"
                }
            ],
            "title": "Directory Traversal",
            "from": [
                "snyk@0.0.0",
                "com.mapbox.mapboxsdk:mapbox-android-sdk@6.6.4",
                "com.mapbox.mapboxsdk:mapbox-sdk-turf@3.4.1",
                "com.mapbox.mapboxsdk:mapbox-sdk-core@3.4.1",
                "com.squareup.retrofit2:converter-gson@2.4.0",
                "com.squareup.retrofit2:retrofit@2.4.0"
            ]
        }
    ]
```

snyk运行生成的json文件存放了漏洞的完整信息（见上一模块示例），这里我们截取了相对重要的几条信息存放在数据库中，如上述例子中提取了`identifiers、referernces、title、from`这四条信息

如果想对漏洞数据库存放的信息进行增删，可以对**vuls.py**的如下部分进行修改

```
infodict["identifiers"] = s['vulnerabilities'][i]["identifiers"]
infodict["references"] = s['vulnerabilities'][i]["references"]
infodict["title"] = s['vulnerabilities'][i]["title"]
infodict["from"] = s['vulnerabilities'][i]["from"]
```

## 目前存在的问题

* LibScout仅能检测.jar，而不能检测.so等其他语言的三方库，可能需要对LibScout进行进一步的改进
* snyk现有的漏洞数据库不够全（仅指java语言），仅包含maven仓库，而缺少例如谷歌仓库等其他仓库中第三方库的相关漏洞信息
