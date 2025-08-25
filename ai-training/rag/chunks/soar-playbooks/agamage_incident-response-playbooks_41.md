# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide guidelines or incident response playbook for Worm Infections? [/INST] Sure. Here is the information requested.
Title: : NIST compliant Incident Response Framework Playbook for Worm Infections
1. Preparation
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Define actors, for each entity, who will be involved into the crisis cell. These actors should be documented in a contact list kept permanently up to date. 
Make sure that analysis tools are up, functional (EDR, Antivirus, IDS, logs analyzers), not compromised, and up-to-date. 
Make sure to have architecture map of your networks. 
Make sure that an up-to-date inventory of the assets is available. 
Perform a continuous security watch and inform the people in charge of security about the threat trends.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
2.1 Detect the Infection:
Detect the infection Information coming from several sources should be gathered and analyzed: 
Antivirus logs 
IDS/IPS 
EDR 
Suspicious connection attempts on servers 
High number of locked accounts 
Suspicious network traffic 
Suspicious connection attempts in firewalls 
High increase of support calls 
High load or system freeze 
High volumes of e-mail sent
If one or several of these symptoms have been spotted, the actors defined in the “preparation” step will get in touch and if necessary, create a crisis cell.
2.2 Identify the infection 
Analyze symptoms to identify the malware, its propagation vectors and countermeasures. 
Leads can be found from: 
CERT’s bulletins 
External support contacts (antivirus companies, etc.) 
Security websites 
Threat intelligence capabilities and providers
Notify Chief Information Security Officer. Contact your national CERT and regulators if required.
Assess the perimeter of the infection Define the boundaries of the infection. If possible, identify the business impact of the infection.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
The following actions should be performed and monitored by the crisis management cell: 
3.1 Disconnect the infected area from the Internet. 
Isolate the infected area. Disconnect it from any network. 
If business-critical traffic cannot be disconnected, allow it after ensuring that it cannot be an infection vector or find validated circumventions techniques. 
Neutralize the propagation vectors. A propagation vector can be anything from network traffic to software flaw. Relevant countermeasures have to be applied (patch, traffic blocking, disable devices, etc.). 
For example, the following tools/techniques can be used: 
EDR 
Patch deployment tools (WSUS) 
Windows GPO 
Firewall rules 
Operational procedures 

Repeat steps 2 to 4 on each sub-area of the infected area until the worm stops spreading. If possible, monitor the infection using analysis tools (antivirus console, server logs, support calls). 
The spreading of the malware must be monitored.
3.2 Mobile devices 
Make sure that no laptop, Smartphone or mobile storage can be used as a propagation vector by the malware. If possible, block all their connections. 
Ask end-users to follow directives precisely.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
4.1 Identify 
Identify tools and remediation methods. 
The following resources should be considered: 
Antivirus signature database 
External support contacts 
Security websites 
Yara scan, Loki, DFIR-ORC, ThorLite 
EDR search 
Define a Disinfection Process. The process has to be validated by an external structure, i.e. CERT, SOC, Incident Response team. The most straight-forward way to get rid ofthe worm is to remaster the machine.
4.2 Test 
Test the disinfection process and make sure that it properly works without damaging any service. 
4.3 Deploy 
Deploy the disinfection tools. Several options can be used: 
EDR 
Windows WSUS and GPO 
Antivirus signature deployment 
Manual disinfection 
Vulnerability patching

Warning: some worm can block some of the remediation deployment methods. If so, a workaround must be found. Remediation progress should be monitored by the crisis cell.
5. Recovery: : Objective: Restore the system to normal operations.
Verify all previous steps have been done correctly and get a management approval before following next steps: 
Reopen the network traffic that was used as a propagation method by the malware 
Reconnect sub-areas together 
Reconnect the mobile laptops to the area 
Reconnect the area to your local network 
Reconnect the area to the Internet 

All these steps shall be made in a step-by-step manner and a technical monitoring shall be enforced by the crisis team.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
6.1 Report 
A crisis report should be written and made available to all of the actors of the crisis management cell. 
The following themes should be described: 
Initial cause of the infection 
Actions and timelines of every important event 
What went right 
What went wrong 
Incident cost 
Indicators of compromise</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
