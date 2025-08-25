# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide an incident response playbook for DDOS attack? [/INST] Sure. Here is the information requested.
Title: : DDOS attack Incident Response Playbook
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
1.1 Internet Service Provider Support
Contact your ISP to understand the DDoS mitigation services it offers (free and paid) and what process you should follow.
If possible, subscribe to a redundant Internet connection and to an Anti-DDoS services provider.
Establish contacts with your ISP and law enforcement entities. Make sure that you have the possibility to use an out-of-band communication channel.
Make sure your ISP and DDoS mitigation service have a 24/7 phone support.
1.2 Inventory
Create a whitelist of the IP addresses and protocols you must allow if prioritizing traffic during an attack. Don’t forget to include your critical customers, key partners, etc.
Document your IT infrastructure details, including business owners, IP addresses and circuit IDs, routing settings; prepare a network topology diagram and an asset inventory.
1.3 Network Infrastructure
Design a good network infrastructure without Single Point of Failure or bottleneck.
Deploy a Web Application Firewall to protect against application-layer DDoS.
Distribute DNS servers and other critical services through different AS.
Harden the configuration of network, OS, and application components that may be targeted by DDoS.
Baseline your current infrastructure’s performance, so you can identify the attack faster and more accurately.
Confirm DNS time-to-live (TTL) settings for the systems that might be attacked. Lower the TTLs, if necessary, to facilitate DNS redirection if the original IP addresses get attacked. 600 is a good TTL value.
Depending on the criticality of services, consider setting up a backup that you can switch on in case of issue.
1.4 Internal Contacts
Establish contacts for your IDS, firewall, systems, and network teams.
Collaborate with the business lines to understand business implications of likely DDoS attack scenarios.
Involve your BCP/DR planning team on DDoS incidents.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 Communication
Prepare an internal and an external communication template about DDoS incidents.
Identify channel where this communication will be posted.
The “preparation” phase is to be considered as the most important element of a successful DDoS incident response.
2.2 Analyze the Attack
Keep in mind the DDoS attack could be a smokescreen hiding a more sophisticated and targeted attack.
Check your anti-DDoS service analysis and your scrubbing centre reports:
Understand the logical flow of the DDoS attack and identify the infrastructure components affected by it.
Understand if you are the target of the attack or a collateral victim.
Review the load and log files of servers, routers, firewalls, applications, and other affected infrastructure.
Identify what aspects of the DDoS traffic differentiate it from benign traffic:
Source IP addresses, AS, etc.
Destination ports
URLs
Protocols flags
Network analysis tools can be used to review the traffic: Tcpdump, Tshark, Snort, Netflow, Ntop, MRTG, Cacti, Nagios
If possible, create a NIDS signature to differentiate between benign and malicious traffic.
2.3 Involve Internal and External Actors
Contact your internal teams to learn about their visibility into the attack.
Contact your ISP to ask for help. Be specific about the traffic you’d like to control:
Network blocks involved
Source IP addresses
Protocols
Notify your company’s executive and legal teams.
2.4 Check the Background
Find out whether the company received an extortion demand as a precursor to the attack:
Check for emails in your security email gateway based on a keyword list.
Some threat actors send extortion demands directly to the email addresses in the Whois records of the targeted website.
Look for revendications of the attack on Social Medias.
Search if anyone would have any interest in threatening your company:
Competitors
Ideologically-motivated groups (hacktivists)
Former employees
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
3.1 Containment Actions
If the bottleneck is a particular feature of an application, temporarily disable that feature.
Attempt to throttle or block DDoS traffic as close to the network’s “cloud” as possible via a router, firewall, load balancer, specialized device, etc.
Terminate unwanted connections or processes on servers and routers and tune their TCP/IP settings.
If possible, switch to alternate sites or networks using DNS or another mechanism. Blackhole DDoS traffic targeting the original IP addresses.
Set up an alternate communication channel between you and your users/customers 
If possible, route traffic through a traffic-scrubbing service or product via DNS or routing changes 
Configure egress filters to block the traffic your systems may send in response to DDoS traffic to avoid adding unnecessary packets to the network.
In case of an extortion attempt, try to buy time with the fraudster. For example, explain that you need more time in order to get management approval.
3.2 ISP or Anti-DDoS Service Actions
If the bottleneck is at the ISP’s or anti-DDoS service’s side, only they can take efficient actions. In that case, work closely with your ISP and/or anti-DDoS provider and make sure you share information efficiently.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Remediation Measures
Contact your ISP and/or anti-DDoS provider and make sure that they enforce remediation measures. Possible measures include:
Filtering 
Traffic-scrubbing/Sinkhole/Clean-pipe
IP public balancing/splitting/switching
Blackhole Routing
Technical remediation actions can mostly be enforced by your ISP and/or anti-DDoS provider.
If the attack had a major impact, you may have to make an incident report to regulators.
5. Recovery: : Objective: Restore the system to normal operations.
5.1 Assess the End of the DDoS Condition
Ensure that the impacted services are reachable again.
Ensure that your infrastructure performance is back to your baseline performance.
5.2 Rollback the Mitigation Measures
Switch back traffic to your original network.
Restart stopped services.
Ensure that the recovery-related actions are decided in accordance with the network teams. Bringing up services could have unexpected side effects.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Report
An incident report should be written and made available to all applicable actors. The following topics should be covered:
Initial detection
Actions and timelines of every important event
What went right
What went wrong
Impact from the incident
Indicators of compromise
6.2 Lessons Learned
Actions to improve the DDoS management processes should be defined to capitalize on this experience. Consider what relationships inside and outside your organizations could help you with future incidents.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
