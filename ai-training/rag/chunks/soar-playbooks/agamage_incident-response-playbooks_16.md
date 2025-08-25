# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide guidelines or incident response playbook for Worm Infection? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Worm Infection
1. Preparation: : Objective: Establish contacts, define procedures, gather information to save time during an incident.
Establish Incident Response Team (IRT) Contacts:
Define and document actors for each entity involved in the crisis cell.
Maintain an up-to-date contact list.
Ensure Functionality of Analysis Tools:
Verify EDR, Antivirus, IDS, and log analyzers are functional and up-to-date.
Network Architecture and Asset Inventory:
Maintain an up-to-date network architecture map.
Ensure availability of an up-to-date inventory of assets.
Continuous Security Watch:
Perform continuous security monitoring.
Inform security personnel about threat trends.
2. Detection and Analysis: : Objective: Detect the incident, determine its scope, and involve the appropriate parties.
Detect the Infection:
Gather and analyze information from multiple sources, including Antivirus logs, IDS/IPS, EDR, suspicious connection attempts, high number of locked accounts, suspicious network traffic, and support calls.
Analyze Symptoms:
Identify malware, its propagation vectors, and countermeasures using CERT bulletins, external support contacts, security websites, and threat intelligence providers.
Assess the Perimeter of the Infection:
Define the infection boundaries and identify business impact.
Notify the Chief Information Security Officer.
Contact national CERT and regulators if required.
3. Containment: : Objective: Mitigate the attack’s effects on the targeted environment.
Disconnect Infected Area:
Isolate and disconnect the infected area from any network.
Allow business-critical traffic only if it cannot be an infection vector or after finding validated circumvention techniques.
Neutralize Propagation Vectors:
Apply relevant countermeasures such as patches, traffic blocking, disabling devices using tools like EDR, WSUS, GPO, and Firewall rules.
Monitor Infection:
Monitor the infection using analysis tools until it is contained.
Ensure mobile devices do not become propagation vectors by blocking their connections and instructing end-users accordingly.
4. Eradication: : Objective: Take actions to remove the threat and avoid future incidents.
Identify Remediation Tools:
Consider resources such as antivirus signature databases, external support contacts, security websites, and tools like Yara scan, Loki, DFIR-ORC, ThorLite, and EDR search.
Define and Validate Disinfection Process:
Validate the disinfection process with an external structure like CERT, SOC, or Incident Response team.
Remaster the machine if necessary.
Test Disinfection Process:
Ensure the disinfection process works without damaging any services.
Deploy Disinfection Tools:
Use EDR, WSUS, GPO, antivirus signature deployment, manual disinfection, or vulnerability patching.
5. Recovery: : Objective: Restore the system to normal operations.
Verify Completion of Previous Steps:
Ensure all previous steps are completed correctly and obtain management approval.
Reconnect Systems Step-by-Step:
Reopen network traffic used as propagation methods, reconnect sub-areas, mobile laptops, local network, and finally the Internet.
Ensure technical monitoring by the crisis team during reconnections.
6. Lessons Learned: : Objective: Document the incident’s details, discuss lessons learned, and adjust plans and defenses.
Report:
Write a crisis report available to all crisis management cell actors, covering:
Initial cause of the infection.
Actions and timelines of important events.
What went right and wrong.
Incident cost.
Indicators of compromise.
Capitalize:
Define actions to improve worm infection management processes based on lessons learned.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
