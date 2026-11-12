import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../../core/constants/app_constants.dart';
import 'storage_service.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({required StorageService storageService}) : _storage = storageService;

  final StorageService _storage;

  Future<String> getBaseUrl() async {
    final server = await _storage.getServerUrl();
    return '$server${AppConstants.apiPrefix}';
  }

  Future<Map<String, String>> _buildHeaders({bool isJson = true}) async {
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    if (isJson) {
      headers['Content-Type'] = 'application/json; charset=UTF-8';
    }
    final token = await _storage.getToken();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    final org = await _storage.getOrganization();
    if (org != null && org.id > 0) {
      headers['X-Organization-Id'] = org.id.toString();
    }
    final user = await _storage.getUser();
    if (user != null) {
      headers['X-User-Role'] = user.role;
      if (user.assignedGroupId != null) {
        headers['X-Assigned-Group-Id'] = user.assignedGroupId.toString();
      }
      if (user.assignedFacultyId != null) {
        headers['X-Assigned-Faculty-Id'] = user.assignedFacultyId.toString();
      }
    }
    return headers;
  }

  dynamic _handleResponse(http.Response response) {
    final bodyText = utf8.decode(response.bodyBytes);
    dynamic decoded;
    try {
      decoded = bodyText.isNotEmpty ? jsonDecode(bodyText) : null;
    } catch (_) {
      decoded = bodyText;
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }

    String msg = 'Server xatosi (${response.statusCode})';
    if (decoded is Map && decoded['detail'] != null) {
      msg = decoded['detail'].toString();
    } else if (decoded is Map && decoded['message'] != null) {
      msg = decoded['message'].toString();
    }
    throw ApiException(response.statusCode, msg);
  }

  Future<dynamic> get(String path, {Map<String, String>? queryParams}) async {
    final base = await getBaseUrl();
    final uri = Uri.parse('$base$path').replace(queryParameters: queryParams);
    final headers = await _buildHeaders(isJson: false);
    final response = await http.get(uri, headers: headers).timeout(const Duration(seconds: 15));
    return _handleResponse(response);
  }

  Future<dynamic> post(String path, {Object? body, Map<String, String>? queryParams}) async {
    final base = await getBaseUrl();
    final uri = Uri.parse('$base$path').replace(queryParameters: queryParams);
    final headers = await _buildHeaders(isJson: true);
    final response = await http
        .post(uri, headers: headers, body: body != null ? jsonEncode(body) : null)
        .timeout(const Duration(seconds: 20));
    return _handleResponse(response);
  }

  Future<dynamic> put(String path, {Object? body}) async {
    final base = await getBaseUrl();
    final uri = Uri.parse('$base$path');
    final headers = await _buildHeaders(isJson: true);
    final response = await http
        .put(uri, headers: headers, body: body != null ? jsonEncode(body) : null)
        .timeout(const Duration(seconds: 20));
    return _handleResponse(response);
  }

  Future<dynamic> delete(String path, {Map<String, String>? queryParams}) async {
    final base = await getBaseUrl();
    final uri = Uri.parse('$base$path').replace(queryParameters: queryParams);
    final headers = await _buildHeaders(isJson: false);
    final response = await http.delete(uri, headers: headers).timeout(const Duration(seconds: 15));
    return _handleResponse(response);
  }

  Future<dynamic> uploadPhotoBytes(String path, Uint8List bytes, String filename) async {
    final base = await getBaseUrl();
    final uri = Uri.parse('$base$path');
    final headers = await _buildHeaders(isJson: false);
    final request = http.MultipartRequest('POST', uri)..headers.addAll(headers);
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamed = await request.send().timeout(const Duration(seconds: 30));
    final response = await http.Response.fromStream(streamed);
    return _handleResponse(response);
  }
}
