class DashboardStats {
  final int totalUsers;
  final int totalDevices;
  final int onlineDevices;
  final int todayEntries;
  final int todayExits;
  final int uniquePresent;

  const DashboardStats({
    this.totalUsers = 0,
    this.totalDevices = 0,
    this.onlineDevices = 0,
    this.todayEntries = 0,
    this.todayExits = 0,
    this.uniquePresent = 0,
  });

  int get absentCount => totalUsers > uniquePresent ? totalUsers - uniquePresent : 0;

  factory DashboardStats.fromJson(Map<String, dynamic> json) {
    return DashboardStats(
      totalUsers: (json['total_users'] as num?)?.toInt() ?? 0,
      totalDevices: (json['total_devices'] as num?)?.toInt() ?? 0,
      onlineDevices: (json['online_devices'] as num?)?.toInt() ?? 0,
      todayEntries: (json['today_entries'] as num?)?.toInt() ?? 0,
      todayExits: (json['today_exits'] as num?)?.toInt() ?? 0,
      uniquePresent: (json['unique_present'] as num?)?.toInt() ?? 0,
    );
  }
}
