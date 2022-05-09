#!/bin/bash -ue

elastic_host=$1
for f in $(find elasticsearch/templates -name '*.json'); do
    filename=$(basename -- "$f")
    tpl_name="${filename%.*}"
    curl -XPUT -H "Content-Type: application/json" "${elastic_host}/_template/${tpl_name}" -d @${f}
done
    
