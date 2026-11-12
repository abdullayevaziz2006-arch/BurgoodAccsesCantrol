class OrganizationInfo {
  final int id;
  final String name;
  final String? code;
  final String? logoUrl;
  final String orgType;
  final List<String> modules;

  const OrganizationInfo({
    required this.id,
    required this.name,
    this.code,
    this.logoUrl,
    this.orgType = 'company',
    this.modules = const [],
  });

  bool get isCompany => orgType == 'company' || orgType == 'office' || orgType == 'business';

  factory OrganizationInfo.fromJson(Map<String, dynamic> json) {
    final rawModules = json['modules'];
    List<String> mods = [];
    if (rawModules is List) {
      mods = rawModules.map((e) => e.toString()).toList();
    } else if (rawModules is String) {
      mods = rawModules.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
    }
    return OrganizationInfo(
      id: (json['id'] as num?)?.toInt() ?? 0,
      name: json['name']?.toString() ?? 'Tashkilot',
      code: json['code']?.toString(),
      logoUrl: json['logo_url']?.toString(),
      orgType: json['org_type']?.toString() ?? 'university',
      modules: mods,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'code': code,
        'logo_url': logoUrl,
        'org_type': orgType,
        'modules': modules,
      };
}

class AuthUser {
  final int? id;
  final String username;
  final String role;
  final String fullName;
  final int? assignedGroupId;
  final int? assignedFacultyId;

  const AuthUser({
    this.id,
    required this.username,
    required this.role,
    required this.fullName,
    this.assignedGroupId,
    this.assignedFacultyId,
  });

  bool get isManagerOrAdmin =>
      role == 'superadmin' ||
      role == 'admin' ||
      role == 'direktor' ||
      role == 'otdel_kadr' ||
      role == 'buxgalter' ||
      role == 'dekan' ||
      role == 'tutor';

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: (json['id'] as num?)?.toInt(),
      username: json['username']?.toString() ?? '',
      role: json['role']?.toString() ?? 'staff',
      fullName: json['full_name']?.toString() ?? json['username']?.toString() ?? 'Foydalanuvchi',
      assignedGroupId: (json['assigned_group_id'] as num?)?.toInt(),
      assignedFacultyId: (json['assigned_faculty_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'role': role,
        'full_name': fullName,
        'assigned_group_id': assignedGroupId,
        'assigned_faculty_id': assignedFacultyId,
      };
}

class AuthResponse {
  final bool success;
  final String token;
  final OrganizationInfo? organization;
  final AuthUser user;

  const AuthResponse({
    required this.success,
    required this.token,
    this.organization,
    required this.user,
  });

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    return AuthResponse(
      success: json['success'] == true,
      token: json['token']?.toString() ?? '',
      organization: json['organization'] is Map<String, dynamic>
          ? OrganizationInfo.fromJson(json['organization'] as Map<String, dynamic>)
          : null,
      user: AuthUser.fromJson((json['user'] as Map<String, dynamic>?) ?? {}),
    );
  }
}
