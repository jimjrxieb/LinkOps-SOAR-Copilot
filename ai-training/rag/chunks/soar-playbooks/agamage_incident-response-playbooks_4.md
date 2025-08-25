# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide guidelines or incident response playbook for Worm Infections? [/INST] Sure. Here is the information requested.
Title: : NIST Incident Response Framework Playbook for Worm Infections
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Define Actors:
Identify and document actors for each entity involved in the crisis cell.
Maintain an up-to-date contact list.
Ensure Analysis Tools are Operational:
Verify that EDR, Antivirus, IDS, and log analyzers are functional, not compromised, and up-to-date.
Maintain Network Architecture and Asset Inventory:
Keep an up-to-date network architecture map.
Ensure availability of an up-to-date inventory of assets.
Continuous Security Watch:
Perform continuous security monitoring.
Inform security personnel about threat trends.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
Detect the Infection:
Gather and analyze information from several sources including:
Antivirus logs
IDS/IPS
EDR
Suspicious connection attempts on servers
High number of locked accounts
Suspicious network traffic
Suspicious connection attempts in firewalls
High increase in support calls
High system load or freeze
High volumes of email sent
If one or several of these symptoms have been spotted, the actors defined in the “preparation” step will get in touch and if necessary, create a crisis cell.
Identify the Infection:
Analyze symptoms to identify the malware, its propagation vectors, and countermeasures.
Utilize leads from:
CERT bulletins
External support contacts (antivirus companies, etc.)
Security websites
Threat intelligence capabilities and providers
Assess the Perimeter of the Infection:
Define the boundaries of the infection (e.g., global infection, bounded to a subsidiary, etc.).
Identify the business impact of the infection if possible.
Notify the Chief Information Security Officer.
Contact national CERT and regulators if required.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Disconnect the Infected Area from the Internet:
Isolate the infected area and disconnect it from any network.
If business-critical traffic cannot be disconnected, allow it after ensuring it cannot be an infection vector or find validated circumvention techniques.
Neutralize Propagation Vectors:
Apply relevant countermeasures, such as patches, traffic blocking, and disabling devices using:
EDR
Patch deployment tools (WSUS)
Windows GPO
Firewall rules
Operational procedures
Monitor the Infection: The spreading of the malware must be monitored.
Repeat steps to isolate and neutralize sub-areas until the worm stops spreading.
Ensure no laptops, smartphones, or mobile storage can propagate the malware.
If possible, monitor the infection using analysis tools (antivirus console, server logs, support calls).
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
Identify Tools and Remediation Methods:
Consider resources such as antivirus signature databases, external support contacts, security websites, and tools like Yara scan, Loki, DFIR-ORC, ThorLite, and EDR search.
Be aware that some worms can block remediation methods; find workarounds if necessary.
Define and Validate Disinfection Process:
Validate the disinfection process with an external structure (CERT, SOC, Incident Response team).
The most straightforward way to eliminate the worm is to remaster the machine.
Test the Disinfection Process:
Ensure the disinfection process works without damaging services.
Deploy Disinfection Tools:
Use tools such as EDR, WSUS, GPO, antivirus signature deployment, manual disinfection, or vulnerability patching.
Warning: some worm can block some of the remediation deployment methods. If so, a workaround must be found. Remediation progress should be monitored by the crisis cell.
5. Recovery: : Objective: Restore the system to normal operations.
Verify Completion of Previous Steps:
Ensure all previous steps are completed correctly and obtain management approval.
Reconnect Systems Step-by-Step:
Reopen network traffic used as propagation methods.
Reconnect sub-areas, mobile laptops, local network, and finally the Internet.
Ensure technical monitoring by the crisis team during reconnections.
All these steps shall be made in a step-by-step manner and a technical monitoring shall be enforced by the crisis team.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Report: A crisis report should be written and made available to all of the actors of the crisis management cell.
Write a crisis report covering:
Initial cause of the infection
Actions and timelines of important events
What went right
What went wrong
Incident cost
Indicators of compromise
Capitalize:
Define actions to improve worm infection management processes based on lessons learned.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
