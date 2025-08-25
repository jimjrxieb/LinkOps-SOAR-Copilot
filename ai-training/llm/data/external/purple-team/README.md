---
license: mit
language:
- en
pretty_name: Purple Team Cybersecurity Dataset
size_categories:
- 10K<n<100K
tags:
- code
---

Dataset Card for Purple Team Cybersecurity Dataset

Dataset Summary

The Purple Team Cybersecurity Dataset is a synthetic collection designed to simulate collaborative cybersecurity exercises, integrating offensive (Red Team) and defensive (Blue Team) strategies. It encompasses detailed records of attack events, defense responses, system logs, network traffic, and performance metrics. This dataset serves as a valuable resource for training, analysis, and enhancing organizational security postures.

Dataset Structure

The dataset is organized into the following primary components:
	1.	Attack Events (Red Team)
      •   event_id (INT): Unique identifier for each attack event.
      •   timestamp (DATETIME): Date and time of the attack event.
      •   attack_technique (STRING): MITRE ATT&CK technique used.
      •   attack_category (STRING): Category of attack (e.g., Initial Access, Execution).
      •   target_system (STRING): System or application targeted.
      •   success_status (BOOLEAN): Indicates whether the attack was successful.
	2.	Defense Responses (Blue Team)
      •   response_id (INT): Unique identifier for each defense response.
      •   event_id (INT): Foreign key linking to the attack event.
      •   detection_time (DATETIME): Timestamp when the attack was detected.
      •   response_time (DATETIME): Timestamp when the response was initiated.
      •   detection_method (STRING): Method of detection (e.g., SIEM, IDS).
      •   response_action (STRING): Action taken to mitigate the attack.
      •   effectiveness (INT): Effectiveness score (1-10) of the response.
	3.	System Logs
      •   log_id (INT): Unique identifier for each log entry.
      •   event_id (INT): Foreign key linking to the attack event.
      •   timestamp (DATETIME): Date and time of the log entry.
      •   log_source (STRING): Source of the log (e.g., Windows Event, Syslog).
      •   log_type (STRING): Type of log (e.g., Security, Application).
      •   log_message (TEXT): Full content of the log message.
	4.	Network Traffic
      •   traffic_id (INT): Unique identifier for each traffic record.
      •   event_id (INT): Foreign key linking to the attack event.
      •   timestamp (DATETIME): Date and time of the network traffic.
      •   source_ip (STRING): Source IP address.
      •   destination_ip (STRING): Destination IP address.
      •   protocol (STRING): Network protocol used.
      •   port (INT): Port number.
      •   payload_size (INT): Size of the data payload in bytes.
	5.	Performance Metrics
      •   metric_id (INT): Unique identifier for each metric entry.
      •   event_id (INT): Foreign key linking to the attack event.
      •   detection_time_seconds (INT): Time taken to detect the attack in seconds.
      •   response_time_seconds (INT): Time taken to respond to the attack in seconds.
      •   false_positive_rate (FLOAT): Rate of false positives in detection.
      •   missed_detection_rate (FLOAT): Rate of attacks not detected.

Intended Uses

This dataset is intended for:
   •   Training: Developing and refining cybersecurity defense and response strategies.
   •   Analysis: Studying attack patterns and evaluating defense mechanisms.
   •   Simulation: Creating realistic scenarios for cybersecurity drills and exercises.

Source and Licensing

This dataset is hosted on Hugging Face by Canstralian. For licensing information, please refer to the repository’s README.md file.

Citation

If you utilize this dataset in your research or projects, please provide appropriate credit to the creators as specified in the repository.

For further guidance on creating dataset cards, you can refer to the Hugging Face documentation:
   •   Create a dataset card
   •   Dataset Cards