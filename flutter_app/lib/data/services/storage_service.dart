import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/constants/app_constants.dart';
import '../models/auth_models.dart';

class StorageService {
  Future<String> getServerUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.keyServerUrl) ?? AppConstants.defaultServerUrl;
  }

  Future<void> setServerUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.keyServerUrl, url.trim().replaceAll(RegExp(r'/+$'), ''));
  }

  Future<void> saveSession({
    required String token,
    required AuthUser user,
    OrganizationInfo? organization,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.keyToken, token);
    await prefs.setString(AppConstants.keyUserJson, jsonEncode(user.toJson()));
    if (organization != null) {
      await prefs.setString(AppConstants.keyOrgJson, jsonEncode(organization.toJson()));
    } else {
      await prefs.remove(AppConstants.keyOrgJson);
    }
  }

  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(AppConstants.keyToken);
  }

  Future<AuthUser?> getUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(AppConstants.keyUserJson);
    if (raw == null || raw.isEmpty) return null;
    try {
      return AuthUser.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<OrganizationInfo?> getOrganization() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(AppConstants.keyOrgJson);
    if (raw == null || raw.isEmpty) return null;
    try {
      return OrganizationInfo.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(AppConstants.keyToken);
    await prefs.remove(AppConstants.keyUserJson);
    await prefs.remove(AppConstants.keyOrgJson);
  }
}
