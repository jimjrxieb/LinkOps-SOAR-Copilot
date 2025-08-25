# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate a Ransomware Incident Response Playbook? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Ransomware Infection (NIST Compliant)
1. Preparation: : Determine the members of the Cybersecurity Incident Response Team (CSIRT).
The core CSIRT members should be comprised of individuals responsible for cybersecurity only.
This may include some members of Information Technology roles, depending on the organization size.
The limited size of the core CSIRT is to assist with confidentiality and efficiency.
The core CSIRT may be activated often to investigate security events that may or may not result in an incident.
Assign roles and responsibilities to each member.
Determine extended CSIRT members.
This will often include Legal, Compliance, Public Relations, and Executive Leadership.
Define escalation paths.
Incidents may start as events, or as a lower impact/severity and then increase as more information is gathered. Establishing an escalation path is critical to success.
Evaluate and secure critical system backups.
Backups should be secured prior to any incident.
During the initial stages of any incident, evaluate and confirm that backups are secure and not impacted by the incident.
2. Detection and Analysis: : Isolate infected systems if it is technically feasible.
DO NOT power off machines, as forensic artifacts may be lost.
Preserve the system(s) for further forensic investigation including log review, MFT analysis, deep malware scans, etc.
Investigate malware to determine if it’s running under a user context.
If so, disable this account (or accounts if multiple are in use) until the investigation is complete.
Analyze the malware to determine characteristics that may be used to contain the outbreak.
If available, use a sandboxed malware analysis system to perform analysis.
Note: Network connectivity should not be present for this sandbox system except in very rare circumstances. Network activity from malware may be used to alert an attacker of your investigation.
Observe any attempts at network connectivity, note these as Indicators of Compromise (IoCs).
Observe any files created or modified by the malware, note these as IoCs.
Note where the malware was located on the infected system, note this as an IoC.
Preserve a copy of the malware file(s) in a password protected zip file.
Use the PowerShell “Get-FileHash” cmdlet to get the SHA-256 hash value of the malware file(s).
This hash may also be used to search for community information regarding this malware (i.e., VirusTotal, Hybrid-Analysis, CISCO Talos, etc.)
Additional hash values (SHA1, MD5, etc.) may be gathered to better suit your security tools.
Note these hash values as IoCs.
Use all IoCs discovered to search any available tools in the environment to locate additional infected hosts.
Use all information and IoCs available to search for the initial point of entry.
Determine the first appearance of the malware.
Determine the user first impacted by the malware.
Investigate all available log files to determine the initial date and point of infection.
Analyze all possible vectors for infection.
Focus on known delivery methods discovered during malware analysis (email, PDF, website, packaged software, etc.).
Once the ransomware variant is identified, perform research to determine Tactics, Techniques, and Procedures (TTPs) associated with this variant and/or threat-actor.
Determine if data exfiltration and extortion is common.
Determine the attacker toolkit if possible.
3. Containment: : Use the information about the initial point of entry gathered in the previous phase to close any possible gaps.
Examples: Firewall configuration changes, email blocking rules, user education, etc.
Once the IoCs discovered in the Identification phase have been used to find any additional hosts that may be infected, isolate these devices as well.
Add IoCs (such as hash value) to endpoint protection.
Set to block and alert upon detection.
Submit hash value to community sources to aid in future detection.
NOTE: Clear this process with legal/compliance representatives during each incident, as each malware situation will be different.
Implement any temporary network rules, procedures, and segmentation required to contain the malware.
If additional accounts have been discovered to be involved or compromised, disable those accounts.
4. Eradication: : Preserve artifacts, systems, and relevant backups according to the sensitivity and scale of the incident. These may be important for future forensics.
If rebuilding or replacing physical systems, preserve physical hard disks, solid-state drives, or forensically sound images of those storage drives.
If rebuilding or replacing virtual machines, preserve a copy, full (independent) snapshot, or a backup of the system.
Preserve any volatile data that may have been collected during the identification and containment phases.
This may include log files, backups, malware samples, memory images, etc.
Once all relevant data, equipment, and/or systems have been preserved, replace or rebuild systems accordingly.
5. Recovery: : Restore impacted systems from a clean backup, taken prior to infection if these backups are available.
For systems not restorable from backup, rebuild the machines from a known good image or from bare metal.
Remediate any vulnerabilities and gaps identified during the investigation.
Reset passwords for all impacted accounts and/or create replacement accounts and leave the impacted accounts disabled permanently.
Continue to monitor for malicious activity related to this incident for an extended period.
Alerts should be configured to aid in quick detection and response.
If data exfiltration and extortion were determined to be part of this attack, work with legal counsel to determine next steps.
6. Lessons Learned: : Conduct a meeting after the incident to discuss the following:
What things went well during the investigation?
What things did not go well during the investigation?
What vulnerabilities or gaps in the organization’s security status were identified?
How will these be remediated?
What further steps or actions would have been helpful in preventing the incident?
Review and update security measures:
Network segmentation
Firewall configuration
Application security
Operating System and/or Application patching procedures
Employee, IT, or CSIRT training
Create and distribute an incident report to relevant parties.
A primary, and more technical, report should be completed for the CSIRT.
An executive summary should be completed and presented to the management team.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
