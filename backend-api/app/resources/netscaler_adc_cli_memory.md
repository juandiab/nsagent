# NetScaler ADC CLI Command Reference — LLM Copilot Memory File

> **Source:** NetScaler ADC Command Reference (developer-docs.netscaler.com), Current Release (14.1)
> **Scope:** All 65 command namespaces and their entities
> **Purpose:** Teach an LLM/Copilot the structure, verbs, and syntax of the NetScaler classic CLI (`ns.conf` / Nitro-equivalent CLI), as distinct from the Next-Gen API.

---

## 1. CLI FUNDAMENTALS

### 1.1 Universal Command Grammar
Almost every NetScaler CLI command follows this shape:
```
<verb> <namespace> <entity> [<name>] [-<param> <value>] [-<param> <value> ...]
```
Examples:
```
add lb vserver web_vs HTTP 10.0.0.10 80
set lb vserver web_vs -persistenceType SOURCEIP
bind lb vserver web_vs svc_web1
show lb vserver web_vs
rm lb vserver web_vs
```

### 1.2 Standard Verbs (operations) and what they do
| Verb | Purpose |
|------|---------|
| `add` | Create a new entity/object |
| `rm` | Remove/delete an entity |
| `set` | Modify parameters of an existing entity |
| `unset` | Reset a parameter to its default value |
| `show` | Display configuration and runtime state of an entity (or list all) |
| `bind` | Attach a sub-entity/relationship (e.g., service to vserver) |
| `unbind` | Detach a previously bound relationship |
| `enable` | Activate a feature, entity, or interface |
| `disable` | Deactivate a feature, entity, or interface |
| `stat` | Show real-time statistics counters for an entity |
| `clear` | Clear config/state/stats (e.g., `clear ns config`) |
| `rename` | Rename an existing entity |
| `link` / `unlink` | Link a cert to its issuer (SSL), and reverse |
| `import` / `export` | Bring in / send out files (certs, signatures, themes, etc.) |
| `update` | Refresh dynamic data (e.g., signatures, CRLs) |
| `create` | Generate artifacts (certs, requests, backups, RSA keys) |
| `save` | Persist running config: `save ns config` |
| `switch` | Switch context (e.g., `switch ns configview`) |
| `force` | Force an action (HA failover, cluster sync) |
| `sync` | Synchronize (HA files, cluster, GSLB config) |
| `flush` | Purge a table/cache (DNS, cache, etc.) |
| `count` | Count entities |
| `kill` | Terminate sessions/connections |
| `reset` | Reset state (e.g., SSL FIPS) |
| `install` | Install software/license |
| `apply` | Apply (e.g., apply audit/nslog policies globally — older form) |
| `diff` | Compare configs (e.g., `diff ns config`) |
| `batch` / `source` | Run a sequence of commands from a file |

### 1.3 Common Global Operations
```
save ns config                       # Persist running config to ns.conf
show ns runningConfig                # Display the live running config
show ns ns.conf                      # Show the saved config file
clear ns config [-force] <level>     # basic | extended | full
diff ns config                       # Differences between running and saved
shell                                # Drop to BSD shell
reboot [-warm]                       # Reboot the appliance
shutdown                             # Shut down the appliance
```

### 1.4 Parameter Conventions
- Parameters are prefixed with `-` (e.g., `-persistenceType`).
- Booleans use `ENABLED`/`DISABLED` or `YES`/`NO` depending on the entity.
- Positional args (no `-`) are usually required identifiers (name, type, IP, port).
- `@` in docs marks a required positional parameter.
- Names are case-sensitive, max length typically 127 chars, must begin with alpha/`_`.

---

## 2. CORE TRAFFIC MANAGEMENT

### 2.1 `lb` — Load Balancing
**Entities:** lb-vserver, lb-service*(via basic)*, lb-monitor, lb-group, lb-metricTable, lb-monbindings, lb-parameter, lb-persistentSessions, lb-policy, lb-policylabel, lb-profile, lb-route, lb-route6, lb-sipParameters, lb-wlm, lb-action, lb-global

**Key commands:**
```
# Virtual server
add lb vserver <name> <serviceType> [<IPAddress> <port>]
    -persistenceType <NONE|SOURCEIP|COOKIEINSERT|SSLSESSION|RULE|URLPASSIVE|...>
    -lbMethod <ROUNDROBIN|LEASTCONNECTION|LEASTRESPONSETIME|URLHASH|...>
    -cltTimeout <secs>
set lb vserver <name> -lbMethod LEASTCONNECTION -persistenceType SOURCEIP
rm lb vserver <name>
enable lb vserver <name>
disable lb vserver <name>
show lb vserver [<name>]
stat lb vserver [<name>]
bind lb vserver <name> <serviceName>
bind lb vserver <name> -policyName <p> -priority <n> [-gotoPriorityExpression <e>]
unbind lb vserver <name> <serviceName>

# Monitor
add lb monitor <name> <type>   # PING, TCP, HTTP, HTTPS, HTTP-ECV, TCP-ECV, DNS, etc.
    -respCode <codes> -httpRequest "<req>" -interval <n> -resptimeout <n>
set lb monitor <name> <type> -interval 5 -resptimeout 3
bind lb monitor <monitorName> <serviceName>

# Group / parameter / persistence
add lb group <name> -persistenceType SOURCEIP
set lb parameter -sessionsThreshold <n> -lbMethod LEASTCONNECTION
show lb persistentSessions [<vserver>]
clear lb persistentSessions [<vserver>]

# Routes
add lb route <network> <netmask> <gatewayName>
add lb route6 <network> <gatewayName>
```
`serviceType` values: HTTP, SSL, TCP, UDP, SSL_TCP, SSL_BRIDGE, DNS, DNS_TCP, SIP_UDP, SIP_TCP, RTSP, RADIUS, DIAMETER, MYSQL, MSSQL, ANY, etc.

### 2.2 `cs` — Content Switching
**Entities:** cs-vserver, cs-policy, cs-action, cs-policylabel, cs-parameter

```
add cs vserver <name> <serviceType> <IPAddress> <port>
    -caseSensitive <ON|OFF>
add cs action <name> -targetLBVserver <lbName>
add cs policy <name> -rule "<expr>" -action <actionName>
bind cs vserver <csName> -policyName <p> -priority <n> [-targetLBVserver <lb>]
bind cs vserver <csName> -lbvserver <defaultLB>     # default target
set cs vserver <name> -spilloverPersistence ON
show cs vserver [<name>]
stat cs vserver [<name>]
```

### 2.3 `cr` — Cache Redirection
**Entities:** cr-vserver, cr-policy, cr-action, cr-commands
```
add cr vserver <name> <serviceType> <IP> <port> -cacheType <TRANSPARENT|REVERSE|FORWARD>
add cr policy <name> -rule "<expr>" -action <CACHE|NOCACHE|...>
add cr action <name> ...
bind cr vserver <name> -policyName <p>
bind cr vserver <name> <cacheServerSvc>
```

### 2.4 `basic` — Servers, Services, Service Groups, VServers
**Entities:** server, service, serviceGroup, serviceGroupMember, vserver, dbsMonitors, location*, nstrace, radiusNode, reporting, svcbindings, servicegroupbindings

```
add server <name> <IPAddress|domain>
add service <name> <serverName|IP> <serviceType> <port>
    -gslb NONE -maxClient <n> -healthMonitor YES -cltTimeout <n>
add serviceGroup <name> <serviceType> -cacheType SERVER
bind serviceGroup <sgName> <serverName|IP> <port>
bind serviceGroup <sgName> -monitorName <mon>
set service <name> -maxClient 100
enable service <name>
disable service <name> [-delay <secs>] [-graceFul YES]
show service [<name>]
stat service [<name>]
show server [<name>]

# nstrace (packet capture)
start nstrace -size 0 -mode RX TX
stop nstrace
show nstrace
```

---

## 3. SSL / TLS

### 3.1 `ssl` — SSL/TLS
**Entities:** ssl-vserver, ssl-service, ssl-serviceGroup, ssl-certKey, ssl-cert, ssl-certBundle, ssl-certChain, ssl-certFile, ssl-certKeyBundle, ssl-certLink, ssl-certReq, ssl-cipher, ssl-ciphersuite, ssl-crl, ssl-crlFile, ssl-dhFile, ssl-dhParam, ssl-dtlsProfile, ssl-ecdsaKey, ssl-fips, ssl-fipsKey, ssl-fipsSIMSource, ssl-fipsSIMTarget, ssl-global, ssl-hsmKey, ssl-keyFile, ssl-logprofile, ssl-ocspResponder, ssl-parameter, ssl-pkcs12, ssl-pkcs8, ssl-policy, ssl-policylabel, ssl-profile, ssl-rsakey, ssl-wrapkey, ssl-caCertGroup, ssl-action

```
# Certificate-key pair
add ssl certKey <certkeyName> -cert <certFile> -key <keyFile>
    [-passcrypt <pass>] [-inform PEM|DER] [-expiryMonitor ENABLED -notificationPeriod 30]
link ssl certKey <certkeyName> <caCertkeyName>     # build chain to issuer
unlink ssl certKey <certkeyName>
update ssl certKey <certkeyName> -cert <newCert> -key <newKey>   # cert rollover

# Bind cert to SSL vserver / service
bind ssl vserver <vsName> -certkeyName <certkey> [-SNICert]
bind ssl service <svcName> -certkeyName <certkey>

# SSL profile & parameters
add ssl profile <name> -sslProfileType FrontEnd|BackEnd -tls13 ENABLED
set ssl profile <name> -ssl3 DISABLED -tls1 DISABLED -tls11 DISABLED -tls12 ENABLED -tls13 ENABLED
set ssl vserver <vsName> -sslProfile <name>
set ssl parameter -defaultProfile ENABLED      # required before Next-Gen API enable

# Ciphers
add ssl cipher <groupName>
bind ssl cipher <groupName> -cipherName <cipher>
bind ssl vserver <vsName> -cipherName <cipherGroup>

# RSA key / CSR / self-signed cert generation
create ssl rsakey <keyFile> <bits> -exponent F4 -keyform PEM
create ssl certReq <reqFile> -keyFile <key> -countryName <C> -organizationName <O> -commonName <CN>
create ssl cert <certFile> <reqFile> <ROOT_CERT|...> -keyFile <key> -days <n>

# CRL / OCSP
add ssl crl <crlName> <crlFile> -inform PEM
add ssl ocspResponder <name> -url <http://...> -cache ENABLED -cacheTimeout <min>
bind ssl certKey <certkey> -ocspResponder <name> -priority <n>

# Operations
show ssl certKey [<name>]
show ssl vserver [<name>]
stat ssl
```

---

## 4. NETWORKING

### 4.1 `network` — L2/L3 Networking
**Entities:** L2Param, L3Param, L4Param, MapBmr, MapDmr, MapDomain, appAlgParam, arp, arpparam, bridge, bridgegroup, bridgetable, channel, ci, fis, forwardingSession, inat, inatparam, inatsession, interface, interfacePair, ip6Tunnel, ip6TunnelParam, ipTunnel, ipTunnelParam, ipset, ipv6, lacp, linkset, nat64, nat64param, nd6, nd6RAvariables, netProfile, netbridge, onLinkIPv6Prefix, portallocation, ptp, rnat, rnat6, rnatglobal, rnatip, rnatparam, rnatsession, route, route6, rsskeytype, tunnelip, tunnelip6, vlan, vrID, vrID6, vrIDParam, vxlan, vxlanVlanMap

```
# VLANs and interfaces
add vlan <id> [-aliasName <name>]
bind vlan <id> -ifnum <interface> [-tagged]
bind vlan <id> -IPAddress <ip> <netmask>
set interface <id> -speed AUTO -duplex FULL -tagall ON
show interface [<id>]
enable interface <id>
disable interface <id>

# Channels (link aggregation)
add channel <id> -ifnum <if1> <if2> -lacpMode ACTIVE -lacpKey <n>

# Routing
add route <network> <netmask> <gateway> [-cost <n>] [-advertise ENABLED]
add route6 <network> <gateway>
add netProfile <name> -srcIp <ip>     # source-IP selection for back-end
bind netProfile ...

# RNAT / INAT
add rnat <name> -network <net> -netmask <mask> -natIP <ip>
add inat <name> <publicIP> <privateIP> -tcpproxy ENABLED

# Tunnels
add ipTunnel <name> <remoteIP> <remoteMask> <localIP> -protocol GRE|IPIP|...
add netbridge <name>
add vxlan <id> -port <n>

# Forwarding session
add forwardingSession <name> -network <net> -netmask <mask>
```

### 4.2 `ns` — System/NetScaler Core
**Entities (selected):** ns-ip, ns-ip6, ns-acl, ns-acl6, ns-acls, ns-simpleacl, ns-mode, ns-feature, ns-config, ns-hostName, ns-httpParam, ns-httpProfile, ns-tcpParam, ns-tcpProfile, ns-tcpbufParam, ns-pbr, ns-pbr6, ns-rpcNode, ns-trafficDomain, ns-license, ns-capacity, ns-partition, ns-limitIdentifier, ns-limitSelector, ns-encryptionParams, ns-encryptionKey, ns-hmacKey, ns-extension, ns-variable, ns-assignment, ns-diameter, ns-icapProfile, ns-runningConfig, ns-savedConfig, ns-version, ns-info, ns-hardware, ns-memory, ns-timezone, ns-weblogparam, ns-param, reboot, shutdown

```
# IP addresses
add ns ip <IPAddress> <netmask> -type <SNIP|VIP|MIP|NSIP|GSLBsiteIP>
add ns ip6 <IPv6Address> -type ...
set ns ip <IPAddress> -mgmtAccess ENABLED -gui ENABLED -ssh ENABLED

# Modes and features
enable ns mode <MODE>      # L3, USNIP, MBF, Edge, USIP, FR, etc.
disable ns mode <MODE>
enable ns feature <FEATURE>  # LB, CS, SSL, GSLB, REWRITE, RESPONDER, AAA, CMP, AppFw, etc.
disable ns feature <FEATURE>
show ns feature
show ns mode

# Profiles & params
add ns tcpProfile <name> -WS ENABLED -SACK ENABLED -mss <n>
add ns httpProfile <name> -dropInvalReqs ENABLED -http2 ENABLED
set ns tcpParam -WS ENABLED
set ns param -timezone "GMT+..." 

# ACLs / PBR
add ns acl <name> <ALLOW|DENY> -srcIP <ip> -destIP <ip> -protocol TCP -priority <n>
apply ns acls
add ns pbr <name> <ALLOW|DENY> -nextHop <ip> -srcIP <ip>
apply ns pbrs

# Rate limiting
add ns limitIdentifier <name> -threshold <n> -timeSlice <ms> -mode REQUEST_RATE -limitType SMOOTH|BURSTY
add ns limitSelector <name> "<expr1>" "<expr2>"

# Admin partitions / traffic domains
add ns partition <name> -maxBandwidth <n> -maxConn <n>
add ns trafficDomain <id> -aliasName <name>

# Info / state
show ns ip
show ns version
show ns hardware
show ns runningConfig
stat ns
```

### 4.3 `ha` — High Availability
**Entities:** HA-node, HA-failover, HA-sync, HA-files, HA-syncFailures
```
add ha node <id> <peerNSIP>
set ha node -haStatus <ENABLED|STAYPRIMARY|STAYSECONDARY> -haSync ENABLED -failSafe ON
force ha failover [-force]
force ha sync
sync ha files [<mode>]    # all, ssl, bookmarks, etc.
show ha node
```

### 4.4 `cluster` — Clustering
**Entities:** cluster-instance, cluster-node, cluster-nodegroup, cluster-files, cluster-sync, cluster-propstatus, cluster-syncFailures
```
add cluster instance <clId> [-preemption ENABLED]
add cluster node <nodeId> <NSIP> -state ACTIVE -backplane <if>
enable cluster instance <clId>
join cluster -clip <CLIP> -password <pw>   # (run on joining node)
add cluster nodegroup <name>
force cluster sync
show cluster instance
show cluster node
```

---

## 5. POLICY ENGINE & APP EXPERT

### 5.1 `policy` — Policy Infrastructure (PI/PIXL Expressions)
**Entities:** policy-expression, policy-patset, policy-patsetFile, policy-dataset, policy-stringmap, policy-urlset, policy-map, policy-httpCallout, policy-param, policy-evaluation
```
add policy expression <name> "<PIXL_expr>"
add policy patset <name>
bind policy patset <name> <string> [-index <n>]
add policy dataset <name> <type>     # ipv4, number, ulong, ipv6
bind policy dataset <name> <value>
add policy stringmap <name>
bind policy stringmap <name> <key> <value>
add policy urlset <name>
import policy urlset <name> -url <http://...>
add policy httpCallout <name> -IPAddress <ip> -port <n> -returnType BOOL|TEXT|NUM
    -hostExpr "<e>" -urlStemExpr "<e>" -resultExpr "<e>"
show policy expression [<name>]
```

### 5.2 `responder`
**Entities:** responder-action, responder-policy, responder-policylabel, responder-htmlpage, responder-param, responder-global
```
add responder action <name> <type> "<targetExpr>"   # respondwith, redirect, respondwithhtmlpage, noop, drop, reset
add responder policy <name> "<rule>" <actionName|DROP|RESET|NOOP>
bind responder global <policyName> <priority> [<gotoExpr>] [-type REQ_DEFAULT]
bind lb vserver <vs> -policyName <policy> -priority <n> -type REQUEST
import responder htmlpage <name> <src>
```

### 5.3 `rewrite`
**Entities:** rewrite-action, rewrite-policy, rewrite-policylabel, rewrite-param, rewrite-global
```
add rewrite action <name> <type> <target> [<stringBuilderExpr>]
    # replace, insert_http_header, delete_http_header, replace_all, corrupt_http_header, insert_before, insert_after
add rewrite policy <name> "<rule>" <actionName>
bind rewrite global <policyName> <priority> [<gotoExpr>] -type RES_DEFAULT
bind lb vserver <vs> -policyName <p> -priority <n> -gotoPriorityExpression NEXT -type RESPONSE
```

### 5.4 `transform`
**Entities:** transform-profile, transform-action, transform-policy, transform-policylabel, transform-global
```
add transform profile <name> -type URL
add transform action <name> <profileName> -priority <n> -reqUrlFrom "<e>" -reqUrlInto "<e>"
add transform policy <name> "<rule>" <profileName>
```

### 5.5 `cmp` — Compression
**Entities:** cmp-action, cmp-policy, cmp-policylabel, cmp-parameter, cmp-global
```
add cmp action <name> <COMPRESS|NOCOMPRESS|GZIP|DEFLATE>
add cmp policy <name> -rule "<expr>" -resAction <actionName>
bind cmp global <policyName> -priority <n>
set cmp parameter -cmpLevel optimal|bestspeed|bestcompression
```

### 5.6 `cache` — Integrated Caching
**Entities:** cache-contentGroup, cache-policy, cache-policylabel, cache-action*(via policy)*, cache-selector, cache-object, cache-forwardProxy, cache-global, cache-parameter
```
add cache contentGroup <name> -relExpiry <secs> -heurExpiryParam <n>
add cache selector <name> "<expr1>" "<expr2>"
add cache policy <name> -rule "<expr>" -action CACHE|NOCACHE|MAYCACHE|MAYNOCACHE -storeInGroup <cg>
bind cache global <policyName> -priority <n> -type REQ_DEFAULT
flush cache contentGroup <name>
show cache object
```

### 5.7 `appqoe` — AppQoE (priority queuing / surge protection)
**Entities:** appqoe-action, appqoe-policy, appqoe-parameter, appqoe-CustomResp
```
add appqoe action <name> -priority HIGH|MEDIUM|LOW -respondWith NS|...  -maxConn <n> -delay <us>
add appqoe policy <name> -rule "<expr>" -action <actionName>
```

### 5.8 `spillover`
**Entities:** spillover-action, spillover-policy
```
add spillover action <name> -action SPOLICY_BASED_SPILLOVER
add spillover policy <name> -rule "<expr>" -action <actionName>
bind lb vserver <vs> -policyName <so> -type SPILLOVER
```

### 5.9 `feo` — Front-End Optimization
**Entities:** feo-action, feo-policy, feo-global, feo-parameter
```
add feo action <name> -pageExtendCache -imgShrinkToAttrib -cssMinify
add feo policy <name> "<rule>" <actionName>
```

---

## 6. SECURITY

### 6.1 `appfw` — Application Firewall (WAF)
**Entities (selected):** appfw-profile, appfw-policy, appfw-policylabel, appfw-global, appfw-settings, appfw-signatures, appfw-fieldType, appfw-confidField, appfw-customSettings, appfw-learningdata, appfw-learningsettings, appfw-archive, appfw-htmlerrorpage, appfw-jsonerrorpage, appfw-xmlerrorpage, appfw-JSONContentType, appfw-XMLContentType, appfw-wsdl, appfw-xmlschema, appfw-protofile, appfw-transactionRecords, appfw-stats
```
add appfw profile <name> -type HTML XML JSON -defaults basic|advanced
set appfw profile <name> -startURLAction block log stats
    -SQLInjectionAction block log stats -crossSiteScriptingAction block log stats
add appfw policy <name> "<rule>" <profileName>
bind appfw global <policyName> <priority>
bind lb vserver <vs> -policyName <appfwPolicy> -priority <n> -type REQUEST
import appfw signatures <src> <name>
update appfw signatures <name>
show appfw profile [<name>]
stat appfw profile <name>
```

### 6.2 `botmgmt` — Bot Management
**Entities:** bot-profile, bot-policy, bot-policylabel, bot-global, bot-settings, bot-signature, bot-stats
```
add bot profile <name> -signatureNTLPMode ON -errorURL <url>
set bot profile <name> -deviceFingerprint ON -trapInsertion ON
add bot policy <name> -rule "<expr>" -profileName <profile>
bind bot global -policyName <p> -priority <n>
import bot signature <src> <name>
update bot signature <name>
```

### 6.3 `aaa` — Authentication, Authorization, Auditing (Traffic-side)
**Entities:** aaa-user, aaa-group, aaa-parameter, aaa-global, aaa-session, aaa-ssoprofile, aaa-certParams, aaa-ldapParams, aaa-radiusParams, aaa-tacacsParams, aaa-kcdAccount, aaa-otpparameter, aaa-preauthenticationaction, aaa-preauthenticationpolicy, aaa-preauthenticationparameter
```
add aaa user <username> [-password <pw>]
add aaa group <groupName>
bind aaa group <groupName> -userName <user>
bind aaa group <groupName> -policy <authzPolicy> -priority <n>
set aaa parameter -maxAAAUsers <n> -enableSessionStickiness YES
add aaa kcdAccount <name> -realmStr <REALM> -delegatedUser <u> -kcdPassword <pw>
show aaa session
kill aaa session [-all]
```

### 6.4 `authentication` — Authentication Policies/Actions (nFactor)
**Entities (selected):** authentication-vserver, authentication-Policy, authentication-policylabel, authentication-authnProfile, authentication-ldapAction, authentication-ldapPolicy, authentication-radiusAction, authentication-radiusPolicy, authentication-tacacsAction, authentication-tacacsPolicy, authentication-samlAction, authentication-samlPolicy, authentication-samlIdPProfile, authentication-samlIdPPolicy, authentication-OAuthAction, authentication-OAuthIDPProfile, authentication-OAuthIdPPolicy, authentication-certAction, authentication-certPolicy, authentication-loginSchema, authentication-loginSchemaPolicy, authentication-epaAction, authentication-noAuthAction, authentication-negotiateAction, authentication-webAuthAction, authentication-captchaAction, authentication-pushService, authentication-azureKeyVault, authentication-dfaAction, authentication-emailAction
```
add authentication vserver <name> SSL <IP> <port>
add authentication authnProfile <name> -authnVsName <vs>
add authentication ldapAction <name> -serverIP <ip> -ldapBase "<dn>" -ldapBindDn "<dn>"
    -ldapBindDnPassword <pw> -ldapLoginName sAMAccountName -ssoNameAttribute userPrincipalName
add authentication Policy <name> -rule "<expr>" -action <ldapAction>
add authentication loginSchema <name> -authenticationSchema <file.xml>
add authentication loginSchemaPolicy <name> -rule <expr> -action <schema>
bind authentication vserver <vs> -policy <p> -priority <n> -nextFactor <label> -gotoPriorityExpression NEXT
add authentication policylabel <name> -loginSchema <schema>   # nFactor factor
bind authentication policylabel <label> -policyName <p> -priority <n> -nextFactor <next>
add authentication samlAction <name> -samlIdPCertName <cert> -samlRedirectUrl <url> -samlIssuerName <name>
```

### 6.5 `authorization`
**Entities:** authorization-action, authorization-policy, authorization-policylabel
```
add authorization action <name> ...
add authorization policy <name> "<rule>" <ALLOW|DENY|actionName>
bind aaa group <grp> -policy <authzPolicy> -priority <n>
```

### 6.6 `tm` — Traffic Management (AAA-TM / SSO)
**Entities:** tm-sessionAction, tm-sessionPolicy, tm-sessionParameter, tm-trafficAction, tm-trafficPolicy, tm-formSSOAction, tm-samlSSOProfile, tm-global
```
add tm sessionAction <name> -sessTimeout <min> -defaultAuthorizationAction ALLOW -SSO ON
add tm sessionPolicy <name> "<rule>" <sessionAction>
add tm trafficAction <name> -SSO ON -formSSOAction <ssoAct>
add tm trafficPolicy <name> "<rule>" <trafficAction>
add tm formSSOAction <name> -actionURL <url> -userField <f> -passwdField <f> -ssoSuccessRule "<e>"
```

### 6.7 `vpn` — Gateway (NetScaler Gateway)
**Entities (selected):** vpn-vserver, vpn-global, vpn-parameter, vpn-sessionAction, vpn-sessionPolicy, vpn-trafficAction, vpn-trafficPolicy, vpn-intranetApplication, vpn-nextHopServer, vpn-url, vpn-urlAction, vpn-urlPolicy, vpn-clientlessAccessPolicy, vpn-clientlessAccessProfile, vpn-portaltheme, vpn-eula, vpn-formSSOAction, vpn-samlSSOProfile, vpn-alwaysONProfile, vpn-epaprofile, vpn-pcoipProfile, vpn-pcoipVserverProfile, vpn-sfconfig, vpn-icaConnection
```
add vpn vserver <name> SSL <IP> <port>
add vpn sessionAction <name> -transparentInterception OFF -SSO ON -icaProxy ON
    -wihome <storefrontURL> -ntDomain <dom> -clientlessVpnMode ON
add vpn sessionPolicy <name> "<rule>" <sessionAction>
bind vpn vserver <vs> -policy <sessionPolicy> -priority <n>
bind vpn vserver <vs> -staServer <https://sta>
add vpn url <name> <linkName> <actualURL>
bind vpn vserver <vs> -urlName <name>
add vpn intranetApplication <name> <protocol> <destIP> -netmask <mask>
show vpn vserver [<name>]
show vpn icaConnection
stat vpn
```

### 6.8 `contentinspection` — Content Inspection (ICAP / IDS-IPS)
**Entities:** contentInspection-action, contentInspection-policy, contentInspection-policylabel, contentInspection-profile, contentInspection-callout, contentInspection-global, contentInspection-parameter
```
add contentInspection profile <name> -type INLINEINSPECTION|MIRROR -egressInterface <if> -ingressInterface <if>
add contentInspection action <name> -type ICAP -serverName <svc> -icapProfileName <p>
add contentInspection policy <name> -rule "<expr>" -action <actionName>
bind contentInspection global <policyName> -priority <n> -type REQUEST
```

### 6.9 `urlfiltering`
**Entities:** urlfiltering-parameter, urlfiltering-Categories, urlfiltering-CategoryGroups, urlfiltering-Categorization
```
set urlfiltering parameter -HoursBetweenDBUpdates <n> -CloudHost <host>
show urlfiltering Categories
show urlfiltering Categorization
```

### 6.10 `reputationservice`
**Entities:** reputation-settings
```
set reputation settings ...
show reputation settings
```

---

## 7. DNS & GSLB

### 7.1 `dns`
**Entities (selected):** dns-nameServer, dns-addRec, dns-aaaaRec, dns-cnameRec, dns-mxRec, dns-nsRec, dns-ptrRec, dns-soaRec, dns-srvRec, dns-txtRec, dns-caaRec, dns-naptrRec, dns-nsecRec, dns-action, dns-action64, dns-policy, dns-policy64, dns-policylabel, dns-profile, dns-parameter, dns-global, dns-view, dns-zone, dns-key, dns-suffix, dns-subnetcache, dns-records, dns-proxyRecords
```
add dns nameServer <IPAddress> [-local]
add dns addRec <hostName> <IPAddress>          # A record
add dns aaaaRec <hostName> <IPv6Address>
add dns cnameRec <aliasName> <canonicalName>
add dns mxRec <domain> -mx <mailExchanger> -pref <n>
add dns soaRec <domain> -originServer <ns> -contact <email>
add dns nsRec <domain> <nameServer>
add dns action <name> <actionType> -viewName <view> | -IPAddress <ips>
add dns policy <name> "<rule>" <actionName>
bind dns global -policyName <p> -priority <n> -type REQ_DEFAULT
add dns zone <zoneName> -proxyMode YES -dnssecOffload ENABLED
flush dns proxyRecords
show dns addRec
```

### 7.2 `gslb` — Global Server Load Balancing
**Entities:** gslb-vserver, gslb-service, gslb-serviceGroup, gslb-serviceGroupMember, gslb-site, gslb-domain, gslb-parameter, gslb-config, gslb-runningConfig, gslb-syncStatus, gslb-ldnsentries, gslb-ldnsentry
```
add gslb site <name> <siteIP> -publicIP <ip>
add gslb service <name> <IP|server> <serviceType> <port> -siteName <site> -publicIP <ip>
add gslb vserver <name> <serviceType> -lbMethod RTT|ROUNDROBIN|STATICPROXIMITY|LEASTCONNECTION
bind gslb vserver <name> -serviceName <gslbSvc>
bind gslb vserver <name> -domainName <fqdn> -TTL <secs>
set gslb parameter -ldnsEntryTimeout <secs>
sync gslb config [-preview] [-forceSync <site>]
show gslb vserver [<name>]
show gslb syncStatus
```

---

## 8. ANALYTICS, LOGGING & MONITORING

### 8.1 `appflow`
**Entities:** appflow-action, appflow-collector, appflow-policy, appflow-policylabel, appflow-param, appflow-global
```
add appflow collector <name> -IPAddress <ip> -port <n> -Transport ipfix|logstream
add appflow action <name> -collectors <c1> <c2>
add appflow policy <name> "<rule>" <actionName>
bind appflow global <policyName> <priority> [<gotoExpr>] -type REQ_DEFAULT
set appflow param -templateRefresh <secs> -httpUrl ENABLED -httpCookie ENABLED
```

### 8.2 `audit`
**Entities:** audit-syslogAction, audit-syslogPolicy, audit-syslogParams, audit-syslogGlobal, audit-nslogAction, audit-nslogPolicy, audit-nslogParams, audit-nslogGlobal, audit-messageaction, audit-messages, audit-stats
```
add audit syslogAction <name> <serverIP> -logLevel ALL -serverPort <n> -dateFormat YYYYMMDD
add audit syslogPolicy <name> <rule> <actionName>
bind audit syslogGlobal -policyName <p> -priority <n>
add audit nslogAction <name> <serverIP> -logLevel ALL
add audit messageaction <name> <logLevel> "<stringBuilderExpr>"
set audit syslogParams -serverIP <ip> -logLevel ALL
show audit messages
```

### 8.3 `analytics`
**Entities:** analytics-profile, analytics-global
```
add analytics profile <name> -type webinsight|tcpinsight|securityinsight -collectors <c>
bind analytics global -analyticsProfile <p>
```

### 8.4 `snmp`
**Entities:** snmp-community, snmp-manager, snmp-trap, snmp-alarm, snmp-user, snmp-group, snmp-view, snmp-engineId, snmp-mib, snmp-oid, snmp-option, snmp-stats
```
add snmp community <communityString> <ALL|READONLY|READWRITE|NONE>
add snmp manager <IPAddress> -netmask <mask>
add snmp trap <trapClass> <trapDestination> -communityName <c> -version V2|V3
set snmp alarm <alarmName> -thresholdValue <n> -normalValue <n> -state ENABLED
add snmp user <name> -group <g> -authType SHA -authPasswd <pw> -privType AES
show snmp mib
```

### 8.5 `lldp`
**Entities:** lldp-param, lldp-neighbors, lldp-stats
```
set lldp param -mode TRANSMITTER RECEIVER -holdtimeTxMult <n>
show lldp neighbors
show lldp param
```

### 8.6 `ntp`
**Entities:** ntp-server, ntp-param, ntp-status, ntp-sync
```
add ntp server <IP|FQDN> -minpoll <n> -maxpoll <n>
set ntp param -authentication YES
enable ntp sync
show ntp status
```

### 8.7 `qos`
**Entities:** qos-stats
```
stat qos
show qos
```

---

## 9. PROTOCOLS & OPTIMIZATION

### 9.1 `protocol`
**Entities:** protocol-http, protocol-http2, protocol-http3, protocol-httpBand, protocol-tcp, protocol-udp, protocol-ip, protocol-ipv6, protocol-icmp, protocol-icmpv6, protocol-mptcp, protocol-quic, protocol-quicbridge
```
stat protocol http
stat protocol tcp
stat protocol quic
show protocol httpBand
```

### 9.2 `quic` / `quicbridge`
**Entities:** quic-param, quic-profile, quicBridge-profile
```
add quic profile <name> -maxIdleTimeout <ms> -initialMaxData <n> -congestionCtrlAlgo CUBIC|BBR
set quic param ...
add quicBridge profile <name> ...
```

### 9.3 `ica` — ICA (Citrix protocol optimization)
**Entities:** ica-action, ica-policy, ica-accessprofile, ica-latencyprofile, ica-parameter, ica-global
```
add ica action <name> -accessProfileName <p> -latencyProfileName <l>
add ica policy <name> -rule "<expr>" -action <actionName>
bind ica global -policyName <p> -priority <n>
add ica accessprofile <name> -ClientClipboard DISABLED -ClientDrive DISABLED
```

### 9.4 `rdp` — RDP Proxy
**Entities:** rdp-clientprofile, rdp-serverprofile, rdp-connections
```
add rdp clientprofile <name> -rdpUrlOverrideClient ENABLE -psk <key>
add rdp serverprofile <name> -rdpIP <ip> -rdpPort <n> -psk <key>
bind vpn vserver <vs> -rdpServerProfileName <name>
show rdp connections
```

### 9.5 `videooptimization`
**Entities:** videooptimization-detectionaction, videooptimization-detectionpolicy, videooptimization-detectionpolicylabel, videooptimization-pacingaction, videooptimization-pacingpolicy, videooptimization-pacingpolicylabel, videooptimization-globaldetection, videooptimization-globalpacing, videooptimization-parameter, videooptimization-stats
```
add videooptimization detectionaction <name> -type ...
add videooptimization detectionpolicy <name> -rule "<expr>" -action <a>
bind videooptimization globaldetection -policyName <p> -priority <n>
```

### 9.6 `stream` — Action Analytics
**Entities:** stream-identifier, stream-selector, stream-session
```
add stream selector <name> "<expr1>" "<expr2>"
add stream identifier <name> <selectorName> -interval <min> -sampleCount <n>
show stream identifier <name>
```

### 9.7 `smpp`
**Entities:** smpp-user, smpp-param
```
add smpp user <name> -password <pw>
set smpp param -clientMode TRANSCEIVER -msgQueueMaxSize <n>
```

---

## 10. CARRIER-GRADE / SERVICE PROVIDER

### 10.1 `lsn` — Large Scale NAT (CGNAT)
**Entities (selected):** lsn-client, lsn-pool, lsn-group, lsn-parameter, lsn-appsprofile, lsn-appsattributes, lsn-transportprofile, lsn-static, lsn-session, lsn-deterministicNat, lsn-nat64, lsn-dslite, lsn-rtspalgprofile, lsn-sipalgprofile, lsn-logprofile, lsn-httphdrlogprofile, lsn-ip6profile
```
add lsn client <name>
bind lsn client <name> -network <net> -netmask <mask>
add lsn pool <name> -nhCidrEntryAlloc <n>
bind lsn pool <name> <startIP> <endIP>
add lsn group <name> -clientname <client> -nattype NAPT|DYNAMIC|DETERMINISTIC
bind lsn group <name> -poolname <pool>
show lsn session
```

### 10.2 `subscriber`
**Entities:** subscriber-profile, subscriber-param, subscriber-gxInterface, subscriber-radiusInterface, subscriber-sessions
```
add subscriber profile <subscriberIP> -subscriberRules <r> -subscriptionIdType E164
set subscriber param -interfaceType RadiusAndGxOnSameServer
set subscriber gxInterface -vServerName <vs> -pcrfRealm <realm>
show subscriber sessions
```

### 10.3 `pcp` — Port Control Protocol
**Entities:** pcp-profile, pcp-server, pcp-map
```
add pcp profile <name> -mapping ENABLED -peer ENABLED -minMapLife <secs>
add pcp server <name> <IPAddress> -port <n> -pcpProfile <profile>
```

### 10.4 `ipsec` / `ipsecalg`
**Entities:** ipsec-profile, ipsec-parameter, ipsec-counters / ipsecalg-profile, ipsecalg-session, ipsecalg-counters
```
add ipsec profile <name> -ikeVersion V2 -encAlgo AES -hashAlgo HMAC_SHA256 -lifetime <secs>
set ipsec parameter -ikeVersion V2
add ipsecalg profile <name> -ipsecSessionTimeout <min>
show ipsecalg session
```

### 10.5 `tunnel` — Tunnel Traffic Management
**Entities:** tunnel-global, tunnel-trafficPolicy
```
add tunnel trafficPolicy <name> "<rule>" <action>
bind tunnel global <policyName> -priority <n>
```

### 10.6 `cloudtunnel`
**Entities:** cloudtunnel-parameter, cloudtunnel-vserver
```
set cloudtunnel parameter ...
add cloudtunnel vserver <name> ...
```

---

## 11. PLATFORM, CLOUD & MANAGEMENT

### 11.1 `system` — System Administration
**Entities (selected):** system-user, system-group, system-cmdPolicy, system-parameter, system-global, system-backup, system-restorepoint, system-core, system-session, system-sshkey, system-kek, system-entity, system-counters, system-cpu, system-memory, system-eventhistory, system-bw
```
add system user <username> <password> [-externalAuth ENABLED] [-timeout <secs>]
add system group <groupName> [-timeout <secs>]
bind system group <groupName> -userName <user>
add system cmdPolicy <name> <ALLOW|DENY> "<cmdSpec_regex>"
bind system user <user> -policyName <cmdPolicy> -priority <n>
set system parameter -minPasswordLen <n> -maxClient <n> -doppler DISABLED
create system backup <fileName> -level full|basic [-comment "<c>"]
restore system backup <fileName>
show system user [<name>]
show system core
```
> `system user/group/cmdPolicy` = **management-plane** RBAC (who can run CLI/GUI commands), distinct from `aaa` (traffic-side auth).

### 11.2 `cli`
**Entities:** alias, batch, cli-attribute, cli-mode, cli-prompt, history, source, man, help, whoami, config, exit, quit, cls, unalias
```
set cli mode -color ON
set cli prompt "%u@%h"
alias <aliasName> "<command>"
batch -fileName <file> [-outFile <out>]
source <file>
show cli attribute
whoami
```

### 11.3 `adm` — NetScaler ADM (Application Delivery Management) registration
**Entities:** adm-parameter
```
set adm parameter -serverIP <admIP> -adminProfile <p> -mas YES
show adm parameter
```

### 11.4 `cloud`
**Entities:** cloud-parameter, cloud-profile, cloud-credential, cloud-service, cloud-autoscalegroup, cloud-awsParam, cloud-ngsparameter, cloud-vserverIP, cloud-allowedngsticketprofile, cloud-stats
```
set cloud parameter -controllerFqdn <fqdn> -activationCode <code> -Deployment Production
add cloud profile <name> ...
show cloud stats
```

### 11.5 `azure`
**Entities:** azure-application, azure-keyVault
```
add azure application <name> -clientID <id> -clientSecret <secret> -tenantID <tid>
add azure keyVault <name> -azureVaultName <vault> -azureApplication <app>
```

### 11.6 `autoscale`
**Entities:** autoscale-profile, autoscale-action, autoscale-policy
```
add autoscale profile <name> -type CLOUD ...
add autoscale action <name> -type SCALE_UP -vServer <vs> -profilename <p>
add autoscale policy <name> -rule "<expr>" -action <a>
```

### 11.7 `db` — Database Users (DataStream)
**Entities:** db-user, db-dbProfile
```
add db user <username> -password <pw>
add db dbProfile <name> -interpretQuery YES -stickiness YES
set lb vserver <mysqlVs> -dbProfileName <name>
```

### 11.8 `api`
**Entities:** api-spec, api-specfile
```
add api spec <name> ...
import api specfile <name> <src>
```

### 11.9 `app` — AppExpert Applications / Templates
**Entities:** application
```
add app ... 
show application
```

### 11.10 `endpoint`
**Entities:** endpoint-info
```
show endpoint info
```

### 11.11 `router`
**Entities:** router-dynamicRouting, vtysh
```
# Dynamic routing is configured via the VTYSH shell (Quagga/ZebOS):
vtysh
  configure terminal
  router bgp <ASN>
  ...
show router dynamicRouting
```

### 11.12 `ulfd` — User Log Facility Daemon
**Entities:** ulfd-server
```
add ulfd server <IPAddress> -port <n>
```

### 11.13 `user` — User-defined Protocol Extensions
**Entities:** user-protocol, user-vserver
```
add user protocol <name> -transport TCP -extension <extName>
add user vserver <name> -userProtocol <proto> -IPAddress <ip> -port <n>
```

### 11.14 `utility` — Operational / Diagnostic Tools
**Entities:** ping, ping6, traceroute, traceroute6, scp, shell, install, raid, callhome, grep, techsupport
```
ping <host>
ping6 <host>
traceroute <host>
install ns <url|file>          # software upgrade
show techsupport
shell                          # BSD shell
set callhome -mode ENABLED -emailAddress <email>
```

---

## 12. PIXL / POLICY EXPRESSION QUICK REFERENCE

The classic CLI uses **Policy Infrastructure eXpression Language (PIXL)** in `-rule`, `-filter`, and action targets. Common building blocks:

| Expression | Meaning |
|------------|---------|
| `HTTP.REQ.URL` | Request URL |
| `HTTP.REQ.URL.PATH` | URL path |
| `HTTP.REQ.URL.PATH_AND_QUERY` | Path + query string |
| `HTTP.REQ.HOSTNAME` | Host header |
| `HTTP.REQ.HEADER("<name>")` | A specific request header |
| `HTTP.REQ.METHOD` | HTTP method |
| `HTTP.REQ.COOKIE.VALUE("<name>")` | Cookie value |
| `CLIENT.IP.SRC` | Source IP |
| `CLIENT.IP.SRC.IN_SUBNET(10.0.0.0/8)` | Subnet test |
| `HTTP.RES.STATUS` | Response status code |
| `SYS.TIME` | System time |
| `TRUE` / `FALSE` | Constant booleans |

Common operators / methods:
```
.EQ("x")  .CONTAINS("x")  .STARTSWITH("x")  .ENDSWITH("x")
.SET_TEXT_MODE(IGNORECASE)  .REGEX_MATCH(re#...#)
&& (AND)   || (OR)   ! (NOT)
```
Examples:
```
HTTP.REQ.URL.PATH.STARTSWITH("/account")
HTTP.REQ.HOSTNAME.EQ("www.cloud.com") && HTTP.REQ.HEADER("user-agent").CONTAINS("mobile")
CLIENT.IP.SRC.IN_SUBNET(192.168.0.0/16)
```

---

## 13. STANDARD OPERATION MATRIX (which verbs each entity type supports)

| Entity category | add | rm | set | unset | show | bind | unbind | enable | disable | stat |
|-----------------|-----|----|----|-------|------|------|--------|--------|---------|------|
| vservers (lb/cs/cr/vpn/gslb/authentication) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| services / serviceGroups | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| monitors | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | — | — |
| policies (all modules) | ✔ | ✔ | ✔ | ✔ | ✔ | (via global/vserver) | | — | — | ✔* |
| actions (all modules) | ✔ | ✔ | ✔ | ✔ | ✔ | — | — | — | — | — |
| profiles / parameters | ✔ | ✔ | ✔ | ✔ | ✔ | (some) | | — | — | — |
| global bind points | — | — | ✔ | ✔ | ✔ | ✔ | ✔ | — | — | — |
| features / modes (ns) | — | — | — | — | ✔ | — | — | ✔ | ✔ | — |
| certs/keys (ssl) | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | — | — | — |

`stat*` = where a statistics counter exists.

---

## 14. CRITICAL BEHAVIORAL RULES FOR THE COPILOT

1. **`save ns config` is required** to persist classic-CLI config; unsaved config is lost on reboot. (Contrast: Next-Gen API config is auto-persistent.)
2. **Features must be enabled before use:** `enable ns feature LB CS SSL REWRITE RESPONDER ...` before adding related entities.
3. **Modes are global behaviors:** `enable ns mode MBF USNIP L3 ...`.
4. **Bind order/priority matters** for policies — lower priority number is evaluated first; use `-gotoPriorityExpression NEXT|END|<expr>`.
5. **Policies are inert until bound** — bind to a vserver (classic/advanced bind point), to a policylabel, or to `<module> global`.
6. **`-type` on binds** selects the bind point: REQUEST/RESPONSE (advanced) or REQ_DEFAULT/RES_DEFAULT/REQ_OVERRIDE/RES_OVERRIDE (global).
7. **SSL default profile prerequisite:** `set ssl parameter -defaultProfile ENABLED` is required before enabling the Next-Gen API and before per-vserver SSL profiles take over global settings (this is a one-way, disruptive change — warn the user).
8. **`rm` fails if an entity is referenced** by another (e.g., a cert bound to a vserver, a service bound to an lb vserver). Unbind first.
9. **`unset` ≠ `rm`:** `unset` reverts a single parameter to default; `rm` deletes the whole object.
10. **Management RBAC (`system user/group/cmdPolicy`) is separate from traffic-side AAA (`aaa`, `authentication`).** Don't conflate them.
11. **`stat <entity>`** gives live counters; **`show <entity>`** gives config + summary state. Use the right one.
12. **HA/cluster write operations** belong on the primary/CLIP node; secondary nodes reject most config writes.
13. **Dynamic routing (BGP/OSPF/RIP)** is configured inside `vtysh` (ZebOS), not via native `add` commands.
14. **Expressions:** classic CLI uses PIXL; the Next-Gen API uses Wireshark-style filters. Don't mix syntaxes.
15. **Always confirm `serviceType`/protocol** when creating vservers/services — it's a required positional argument and cannot be changed with `set` (requires delete + recreate).

---

## 15. NAMESPACE INDEX (all 65 sections)

aaa · adm · analytics · api · app · appflow · appfw · appqoe · audit · authentication · authorization · autoscale · azure · basic · botmgmt · cache · cli · cloud · cloudtunnel · cluster · cmp · contentinspection · cr · cs · db · dns · endpoint · feo · gslb · ha · ica · ipsec · ipsecalg · lb · lldp · lsn · network · ns · ntp · pcp · policy · protocol · qos · quic · quicbridge · rdp · reputationservice · responder · rewrite · router · smpp · snmp · spillover · ssl · stream · subscriber · system · tm · transform · tunnel · ulfd · urlfiltering · user · utility · videooptimization · vpn

---

*Note: This reference captures command structure, the canonical verbs, key parameters, and the full entity inventory per namespace for NetScaler ADC 14.1. For exhaustive per-parameter detail on any single entity (every optional flag, value range, and default), consult the corresponding page at developer-docs.netscaler.com. The grammar and bind/priority rules above apply uniformly, so the Copilot can construct valid commands for entities not individually expanded here by following the patterns in Sections 1 and 13.*
