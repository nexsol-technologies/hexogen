

python3 -m venv .venv
python3 -m pip install -r ./python/requirements.txt
source .venv/bin/activate

export CONFIG_FILE=sample/test.yaml
export TEMPLATE_FILE=sample/template.mako
export OUTPUT_PATH=./output/
export DOMAIN_NAME=localdomain
mkdir -p $OUTPUT_PATH
python3 python/hexogen.py testme/test.yaml testme/template.mako output/ localdomain
