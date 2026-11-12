class AccessLog {
  final int id;
  final int deviceId;
  final String? deviceName;
  final int? userId;
  final String? employeeNo;
  final String? userName;
  final String direction;
  final String eventTime;
  final String eventType;
  final String status;
  final String? snapshotUrl;
  final String? photoPath;
  final String? role;
  final String? groupName;
  final String? position;

  const AccessLog({
    required this.id,
    required this.deviceId,
    this.deviceName,
    this.userId,
    this.employeeNo,
    this.userName,
    required this.direction,
    required this.eventTime,
    this.eventType = 'Face Match',
    this.status = 'Success',
    this.snapshotUrl,
    this.photoPath,
    this.role,
    this.groupName,
    this.position,
  });

  String get displayDirection {
    switch (direction.toLowerCase()) {
      case 'break_out':
        return 'Tushlikka chiqish';
      case 'break_in':
        return 'Tushlikdan kirish';
      case 'exit':
        return 'Chiqish';
      case 'entry':
        return 'Kirish';
      default:
        return direction;
    }
  }

  String get formattedTime {
    if (eventTime.length >= 19) {
      return eventTime.substring(11, 19);
    }
    return eventTime;
  }

  String get formattedDate {
    if (eventTime.length >= 10) {
      return eventTime.substring(0, 10);
    }
    return '';
  }

  factory AccessLog.fromJson(Map<String, dynamic> json) {
    return AccessLog(
      id: (json['id'] as num?)?.toInt() ?? 0,
      deviceId: (json['device_id'] as num?)?.toInt() ?? 0,
      deviceName: json['device_name']?.toString(),
      userId: (json['user_id'] as num?)?.toInt(),
      employeeNo: json['employee_no']?.toString(),
      userName: json['user_name']?.toString(),
      direction: json['direction']?.toString() ?? 'entry',
      eventTime: json['event_time']?.toString() ?? '',
      eventType: json['event_type']?.toString() ?? 'Face Match',
      status: json['status']?.toString() ?? 'Success',
      snapshotUrl: json['snapshot_url']?.toString(),
      photoPath: json['photo_path']?.toString(),
      role: json['role']?.toString(),
      groupName: json['group_name']?.toString(),
      position: json['position']?.toString(),
    );
  }
}
