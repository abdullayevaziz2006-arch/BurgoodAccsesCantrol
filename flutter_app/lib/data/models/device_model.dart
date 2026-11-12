class DeviceModel {
  final int id;
  final String name;
  final String ipAddress;
  final int port;
  final String direction;
  final String? universalMode;
  final String? universalOptions;
  final String? lunchStart;
  final String? lunchEnd;
  final String? location;
  final String status;
  final String? model;
  final String? lastSeen;
  final bool isActive;

  const DeviceModel({
    required this.id,
    required this.name,
    required this.ipAddress,
    this.port = 80,
    required this.direction,
    this.universalMode,
    this.universalOptions,
    this.lunchStart,
    this.lunchEnd,
    this.location,
    this.status = 'offline',
    this.model,
    this.lastSeen,
    this.isActive = true,
  });

  bool get isOnline => status.toLowerCase() == 'online';
  bool get isUniversal => direction == 'universal';
  bool get isLunchTerminal =>
      universalMode == 'lunch' ||
      (lunchStart != null && lunchStart!.isNotEmpty);

  String get directionLabel {
    switch (direction) {
      case 'entry':
        return 'Kirish';
      case 'exit':
        return 'Chiqish';
      case 'universal':
        return 'Universal';
      default:
        return direction;
    }
  }

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      id: (json['id'] as num?)?.toInt() ?? 0,
      name: json['name']?.toString() ?? 'Terminal',
      ipAddress: json['ip_address']?.toString() ?? '',
      port: (json['port'] as num?)?.toInt() ?? 80,
      direction: json['direction']?.toString() ?? 'universal',
      universalMode: json['universal_mode']?.toString(),
      universalOptions: json['universal_options']?.toString(),
      lunchStart: json['lunch_start']?.toString(),
      lunchEnd: json['lunch_end']?.toString(),
      location: json['location']?.toString(),
      status: json['status']?.toString() ?? 'offline',
      model: json['model']?.toString(),
      lastSeen: json['last_seen']?.toString(),
      isActive: json['is_active'] != false,
    );
  }
}
