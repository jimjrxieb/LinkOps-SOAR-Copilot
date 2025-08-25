# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please provide a Business Email Compromise Incident response playbook? [/INST] Sure. Here is the information requested.
Title: : Business Email Compromise (BEC) Incident Response Playbook
1. Preparation: : Establish Cybersecurity Incident Response Team (CSIRT).
Identify core CSIRT members responsible for cybersecurity, including necessary Information Technology roles based on organization size.
Keep the core CSIRT small for confidentiality and efficiency.
Activate the core CSIRT frequently to investigate security events.
Assign roles and responsibilities.
Define specific tasks for each CSIRT member to ensure clarity during an incident.
Determine extended CSIRT members.
Include Legal, Compliance, Public Relations, and Executive Leadership.
Define escalation paths.
Set clear paths for escalating incidents from events to higher impact levels.
Configure logging levels for email system components.
Set a minimum of 90 days for log retention.
Store logs in secure locations, preferably on a secondary system like a SIEM.
2. Detection and Analysis: : Assess initial notification and evidence of compromise.
Examples: emails from external clients indicating phishing, unusual email rules, fraudulent transactions, etc.
Determine the method of account compromise.
Interview the impacted user to gather details on suspicious emails, credential entry on suspicious websites, new software installations, unexpected email documents, etc.
Conduct a thorough search for phishing emails.
Look for emails with credential harvesting links and potential malware on the user's workstation (e.g., Mimikatz, keystroke recorders, clipboard scraping malware).
Use Indicators of Compromise (IoCs) to search the environment for other victims.
Query inputs: email subjects, document names, hashes, URLs, etc.
Review email system logs for anomalies.
Investigate login activity from unusual locations, systems, or browser fingerprints.
Compare anomalies with other similar logins (IP address, concurrent logins, browser fingerprints).
Assess victim email accounts for sensitive information.
Extend the search to other sources like OneDrive, Google Drive, SharePoint, shared mailboxes, fileservers, etc.
Consult legal counsel if sensitive information is involved.
Check impacted systems for newly created users.
Ensure all newly created users are legitimate.
3. Containment: : Reset passwords for all identified victims.
Start with email account passwords and extend to all associated accounts.
Revoke authentication tokens for all victim accounts.
Cover email systems and other associated accounts.
Notify external organizations if involved.
Work with legal counsel to notify and block domains from compromised sources.
Block identified domains from sending emails to the organization.
If malware is discovered:
Preserve a sample and analyze it.
Gather file hashes and submit them to community sources like VirusTotal.
Isolate infected systems and preserve them for forensic investigation.
Block associated IoCs in email and endpoint protection systems.
4. Eradication: : Preserve artifacts, systems, and backups according to incident sensitivity.
Retain malicious emails and malware in a secure, password-protected location.
Preserve physical and virtual system components, including hard disks, SSDs, and virtual machine snapshots.
Replace or rebuild systems after preserving relevant data.
5. Recovery: : Remediate vulnerabilities identified during the investigation.
Reset passwords and create replacement accounts as necessary.
Ensure all impacted accounts are handled correctly.
Monitor for malicious activity related to the incident for an extended period.
Configure alerts for quick detection of anomalous behavior.
Consult cybersecurity insurance if financial loss was incurred.
6. Lessons Learned: : Conduct a post-incident meeting to discuss:
Successes and challenges during the investigation.
Identified vulnerabilities and gaps.
Remediation steps.
Additional actions to prevent future incidents.
Review and update security measures:
Application security
OS and application patching procedures
Training for employees, IT, and CSIRT
Email filtering policies
Multifactor Authentication
Email retention policies
Sensitive information policies and procedures
Create and distribute an incident report:
A detailed technical report for the CSIRT.
An executive summary for management.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
