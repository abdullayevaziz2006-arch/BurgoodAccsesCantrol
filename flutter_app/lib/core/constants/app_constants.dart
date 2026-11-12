class AppConstants {
  AppConstants._();

  static const String appName = 'Burgood Access Control';
  static const String defaultServerUrl = 'https://51.21.87.93.sslip.io';
  static const String apiPrefix = '/api/v1';

  // SharedPreferences keys
  static const String keyServerUrl = 'burgood_server_url';
  static const String keyToken = 'burgood_token';
  static const String keyUserJson = 'burgood_user_json';
  static const String keyOrgJson = 'burgood_org_json';

  static String buildWsUrl(String serverUrl) {
    final cleaned = serverUrl.trim().replaceAll(RegExp(r'/+$'), '');
    if (cleaned.startsWith('https://')) {
      return '${cleaned.replaceFirst('https://', 'wss://')}/ws/';
    }
    if (cleaned.startsWith('http://')) {
      return '${cleaned.replaceFirst('http://', 'ws://')}/ws/';
    }
    return 'wss://$cleaned/ws/';
  }

  static String resolveMediaUrl(String serverUrl, String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http://') || path.startsWith('https://')) return path;
    final cleaned = serverUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return '$cleaned$normalizedPath';
  }
}
