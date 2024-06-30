"""Hexogen - HAProxy configuration generator by Nexsol Technologies"""
import sys
import os
from os import environ
import logging
import yaml
from mako.template import Template
from mako.exceptions import RichTraceback

def get_config(file):
    """Load YAML configuration file and return a python dict"""
    logging.info("Reading configuration file %s" , file)
    documents = None
    if os.path.exists(file):
        with open(file, encoding="utf-8") as config_file:
            try:
                documents = yaml.load(config_file, Loader=yaml.FullLoader)
            except yaml.parser.ParserError as inst:
                logging.error ("Error reading config file %s ", inst)
                documents = None
    else:
        logging.error ("Config file %s not found", file)
        documents = None

    return documents

def generate_host_map(yamlconfig, domain_name):
    """Generate a host map"""
    hostmap_str="#domainname    backendname\n"

    # for each service ID
    for service_id in yamlconfig:
        # if servicename contains a domain name, ignore the domain name
        if "." in service_id:
            less_service_id = service_id.split('.', 1)[0]
        else:
            less_service_id = service_id
        backend_name = f"{less_service_id}.{domain_name}"
        full_service_id = backend_name

        maintenance_mode = yamlconfig.get(service_id, {}).get("maintenance")
        if maintenance_mode is True:
            backend_name = "maintenance"

        hostmap_str += f"{full_service_id}  {backend_name}\n"
    return hostmap_str

def generate_defaults(config):
    """Force default values in configuration file"""
    for host in config:
        config[host]['balance'] = config[host].get('balance','roundrobin')
        config[host]['persist'] = config[host].get('persist', False)
        config[host]['cache'] = config[host].get('cache', False)
        config[host]['ssl'] = config[host].get('ssl', False)
        config[host]['checkinter'] = config[host].get('checkinter', "2")
        config[host]['checkfall'] = config[host].get('checkfall', 3)
        config[host]['checkrise'] = config[host].get('checkrise', 2)
        config[host]['group'] = config[host].get('group', 'default').replace (" ", "_")
        config[host]['maintenance'] = config[host].get('maintenance', False)
        config[host]['security'] = config[host].get('security', 'none')
    return config

def check_params():
    """Check configuration"""
    if environ.get('CONFIG_FILE') is None:
        print("CONFIG_FILE environment variable is not set. A valid yaml file is required")
        return False
    elif not os.path.isfile(environ.get('CONFIG_FILE')):
        print("CONFIG_FILE does not exists : %s", environ.get('CONFIG_FILE'))
        return False
    if environ.get('TEMPLATE_FILE') is None:
        print("TEMPLATE_FILE environment variable is not set")
        return False
    elif not os.path.isfile(environ.get('TEMPLATE_FILE')):
        print("TEMPLATE_FILE does not exists : %s", environ.get('TEMPLATE_FILE'))
        return False
    if environ.get('OUTPUT_PATH') is None:
        print("OUTPUT_PATH environment variable is not set")
        return False
    elif not os.path.exists(environ.get('OUTPUT_PATH')):
        print("Output path does not exists : %s", environ.get('OUTPUT_PATH'))
        return False
    if environ.get('DOMAIN_NAME') is None:
        print("DOMAIN_NAME environment variable is not set. Sample : local domain")
        return False
    return True

def generate():
    """Generate HAProxy configuration files"""

    configfile=os.environ['CONFIG_FILE']
    templatefile=os.environ['TEMPLATE_FILE']
    outputdir=os.environ['OUTPUT_PATH']
    domainname=os.environ['DOMAIN_NAME']

    # If everything is checked we can instanciate a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(outputdir+'generate.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    # Load the configuration yaml file
    config=get_config(configfile)
    if config is None:
        sys.exit(1)

    # rendering template
    logging.info("Rendering haproxy configuration with template file %s " , templatefile)
    config = generate_defaults(config)
    try:
        mytemplate = Template(filename=templatefile)
        result=mytemplate.render(config=config, domainname=domainname)
    except:
        traceback = RichTraceback()
        for (filename, lineno, function, line) in traceback.traceback:
            logging.error("File %s, line %s, in %s" ,filename, lineno, function)
            logging.error(line)
        logging.error("%s: %s" , str(traceback.error.__class__.__name__), traceback.error)
        sys.exit(1)

    # save haproxy configuration
    logging.info ("Writing haproxy configuration in %s/%s", outputdir, 'haproxy.conf' )
    with open(outputdir+"haproxy.conf", "w", encoding="utf-8") as f:
        f.write(result)

    # generate hosts.map file
    logging.info ("Writing hostmap configuration in %s/%s", outputdir, 'hosts.map' )
    hostmap=generate_host_map(config, domainname)
    with open(outputdir+"hosts.map", "w", encoding="utf-8") as f:
        f.write(hostmap)

    logging.info ("Generation successfull")

if __name__ == "__main__":
    if not check_params():
        sys.exit(1)
    generate()
