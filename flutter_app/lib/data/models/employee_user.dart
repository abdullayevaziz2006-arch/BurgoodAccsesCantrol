class EmployeeUser {
  final int id;
  final String employeeNo;
  final String fullName;
  final String role;
  final String? position;
  final String? phoneNumber;
  final String? cardNumber;
  final int? departmentId;
  final String? departmentName;
  final int? groupId;
  final String? groupName;
  final String? photoPath;
  final bool isActive;

  const EmployeeUser({
    required this.id,
    required this.employeeNo,
    required this.fullName,
    required this.role,
    this.position,
    this.phoneNumber,
    this.cardNumber,
    this.departmentId,
    this.departmentName,
    this.groupId,
    this.groupName,
    this.photoPath,
    this.isActive = true,
  });

  factory EmployeeUser.fromJson(Map<String, dynamic> json) {
    return EmployeeUser(
      id: (json['id'] as num?)?.toInt() ?? 0,
      employeeNo: json['employee_no']?.toString() ?? '',
      fullName: json['full_name']?.toString() ?? '',
      role: json['role']?.toString() ?? 'staff',
      position: json['position']?.toString(),
      phoneNumber: json['phone_number']?.toString(),
      cardNumber: json['card_number']?.toString(),
      departmentId: (json['department_id'] as num?)?.toInt(),
      departmentName: json['department_name']?.toString(),
      groupId: (json['group_id'] as num?)?.toInt(),
      groupName: json['group_name']?.toString(),
      photoPath: json['photo_path']?.toString(),
      isActive: json['is_active'] != false,
    );
  }
}
