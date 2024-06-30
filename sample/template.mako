global
    fd-hard-limit 50000

defaults
    retries 3
    timeout client 30s
    timeout connect 4s
    timeout server 30s
    mode http

cache mycache
    total-max-size      500     # Total size of the cache in MB
    max-object-size     1000000 # Max size of one object in bytes
    max-age             3600    # Data will persist 1h in the cache 

frontend http_default
    bind *:8080 
    filter compression
    compression algo gzip
    compression type text/css text/html text/javascript application/javascript text/plain 
    use_backend %[req.hdr(host),lower,map_dom(/etc/haproxy/maps/hosts.map,be_default)]

backend maintenance
    balance roundrobin
    server maintenance nginx:80 check

% for host in config:
backend ${host}.${domainname}
    option forwardfor
    % if config[host]['security']=="high-api":
    # OWASP Security for API
    http-response set-header Content-Security-Policy "frame-ancestors 'none'"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header Cache-Control "no-store"
    # let's say the api is a public api, so CORS directive is permissive
    http-response set-header Access-Control-Allow-Origin "*"
    http-response del-header Server
    # in a production environment, providing https access, you should add this header
    http-response set-header Strict-Transport-Security "max-age=16000000; includeSubDomains; preload;"
    # End of security headers
    % endif

    % if config[host]['cache']==True:
    http-request del-header Cache-Control
    http-request cache-use mycache 
    http-response cache-store mycache    
    http-response set-header X-Cache-Status HIT  if !{ srv_id -m found }
    http-response set-header X-Cache-Status MISS if { srv_id -m found }
    % endif

    %if config[host].get('checkurl'):
    option httpchk GET ${config[host]['checkurl']}
    % endif
    %if config[host]['persist']:
    balance source
    hash-type consistent    
    %else:
    balance ${config[host]['balance']}
    %endif
        % for back in config[host]['urls']:
           <% servername=back.replace(":","_") %> <% servername=servername.replace(".","_") %>
    server ${config[host]['group']}_${servername} ${back} check inter ${config[host]['checkinter']}s fall ${config[host]['checkfall']} rise ${config[host]['checkrise']}
        % endfor
% endfor
