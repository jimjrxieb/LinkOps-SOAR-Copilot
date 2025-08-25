# Incident Response Playbook

**Incident Type**: General Incident
**Framework**: NIST

**Playbook Content**:
<s>[INST] <<SYS>>
You are a highly advanced AI assistant in our company responsible for generating detailed incident response playbooks for various types of cyber attacks in OT environment.Please generate a comprehensive incident response playbook for given attacks, adhering to the NIST Special Publication 800-61 Revision 2 guidelines for computer security incident handling.The playbook must adhere to the NIST incident response lifecycle stages - Preparation, Detection and Analysis, Containment, Eradication, Recovery, and Lessons Learned.Each step should describe and elaborate in detail with key practical information to follow in response to a incident
<</SYS>>

Please generate an Incident Response Playbook for a lost or stolen laptop? [/INST] Sure. Here is the information requested.
Title: : Incident Response Playbook for Lost or Stolen Laptop
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
Determine controls for lost or stolen devices.
Implement remote wipe capabilities.
Ensure at-rest encryption.
Enforce Multi-Factor Authentication.
2. Detection and Analysis: : Identify the nature of the device that has been lost or stolen.
Determine if it is a laptop, phone, tablet, or another device such as a desktop, server, or other equipment.
Assess the criticality of data or accounts that may be present on the device.
Interview the user to understand the conditions around the lost or stolen device.
Was it misplaced?
Can you confirm that it was stolen?
Was the device logged in and active to any accounts?
Contact local authorities to report the loss.
Clear this process with legal counsel first.
3. Containment: : Disable or reset the password for any accounts that may be accessed via the lost or stolen device.
Perform remote wipe capabilities to eradicate any sensitive data on the lost or stolen device.
If the device is a laptop or other computer:
Disable any Active Directory accounts for the device.
Create alerts for any time the device contacts the network.
Disable any remote access associated with the device (e.g., VPN accounts and certificates, Microsoft Intune, Exchange ActiveSync, JAMF, etc.).
Remind the user to disable or reset the password for any personal accounts in use on the device.
If the device is a phone, tablet, or other mobile device:
Disable Active Directory accounts for the device if applicable.
Disable any remote access associated with the device (e.g., VPN accounts and certificates, Microsoft Intune, Exchange ActiveSync, JAMF, etc.).
Create alerts for any time the device attempts to check-in or contact the network.
Contact the cellular provider to notify them that the device has been lost or stolen and any associated hardware addresses should be blocked from access.
Remind the user to disable or reset the password for any personal accounts in use on the device.
4. Eradication: : Ensure that remote wipe capabilities have been executed successfully to remove sensitive data from the lost or stolen device.
Verify that all accounts potentially accessible from the lost or stolen device have had their passwords reset or disabled.
Confirm that all remote access points associated with the device have been disabled.
Update any related security policies or procedures as necessary to prevent future incidents.
5. Recovery: : Restore user work functionality with a trusted device.
Create alerts for any abnormal activity from the user accounts involved.
6. Lessons Learned: : Conduct a meeting after the incident to discuss the following:
What things went well during the investigation?
What things did not go well during the investigation?
What vulnerabilities or gaps in the organization’s security status were identified?
How will these be remediated?
What further steps or actions would have been helpful in preventing the incident?
Review and update security measures:
Remote management capabilities
Application security
Employee, IT, or CSIRT training
Encryption capabilities
Access rights to sensitive information
Create and distribute an incident report to relevant parties.
A primary, and more technical, report should be completed for the CSIRT.
An executive summary should be completed and presented to the management team.</s>



**Response Type**: Incident Response
**Category**: SOAR Playbook
**Source**: agamage/incident-response-playbooks
