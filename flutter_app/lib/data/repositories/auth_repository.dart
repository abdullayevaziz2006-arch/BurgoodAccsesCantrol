import '../models/auth_models.dart';
import '../services/api_client.dart';
import '../services/storage_service.dart';

class AuthRepository {
  AuthRepository({
    required ApiClient apiClient,
    required StorageService storageService,
  })  : _api = apiClient,
        _storage = storageService;

  final ApiClient _api;
  final StorageService _storage;

  Future<AuthResponse> login({
    required String username,
    required String password,
    required String serverUrl,
  }) async {
    await _storage.setServerUrl(serverUrl);
    final raw = await _api.post('/auth/login', body: {
      'username': username.trim(),
      'password': password.trim(),
      'app_type': 'android',
    });

    final auth = AuthResponse.fromJson(raw as Map<String, dynamic>);
    if (!auth.success || auth.token.isEmpty) {
      throw const ApiException(401, 'Login yoki parol noto\'g\'ri');
    }

    await _storage.saveSession(
      token: auth.token,
      user: auth.user,
      organization: auth.organization,
    );
    return auth;
  }

  Future<(AuthUser?, OrganizationInfo?, String)> restoreSession() async {
    final token = await _storage.getToken();
    final serverUrl = await _storage.getServerUrl();
    if (token == null || token.isEmpty) {
      return (null, null, serverUrl);
    }
    final user = await _storage.getUser();
    final org = await _storage.getOrganization();
    return (user, org, serverUrl);
  }

  Future<void> logout() => _storage.clearSession();
}
