#!/bin/bash -eu

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cat << EOF
---
# Source: mockserver-config/templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mockserver-config
  labels:
    app: mockserver-config
data:
  mockserver.properties: |
    ###############################
    # MockServer & Proxy Settings #
    ###############################
    
    # Socket & Port Settings
    
    # socket timeout in milliseconds (default 120000)
    mockserver.maxSocketTimeout=120000
    
    # Certificate Generation
    
    # dynamically generated CA key pair (if they don't already exist in specified directory)
    mockserver.dynamicallyCreateCertificateAuthorityCertificate=true
    # save dynamically generated CA key pair in working directory
    mockserver.directoryToSaveDynamicSSLCertificate=.
    # certificate domain name (default "localhost")
    mockserver.sslCertificateDomainName=localhost
    # comma separated list of ip addresses for Subject Alternative Name domain names (default empty list)
    mockserver.sslSubjectAlternativeNameDomains=www.example.com,www.another.com
    # comma separated list of ip addresses for Subject Alternative Name ips (default empty list)
    mockserver.sslSubjectAlternativeNameIps=127.0.0.1
    
    # CORS
    
    # enable CORS for MockServer REST API
    mockserver.enableCORSForAPI=true
    # enable CORS for all responses
    mockserver.enableCORSForAllResponses=true
    
    # Json Initialization
    
    mockserver.initializationJsonPath=/config/initializerJson.json
  initializerJson.json: |
    $(python3 ${SCRIPT_DIR}/generate_mockserver_config.py)
EOF
