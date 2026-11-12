import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../core/constants/app_constants.dart';
import '../models/access_log.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  Timer? _reconnectTimer;
  bool _disposed = false;
  String? _serverUrl;

  final StreamController<AccessLog> _eventController = StreamController<AccessLog>.broadcast();
  Stream<AccessLog> get events => _eventController.stream;

  void connect(String serverUrl) {
    _serverUrl = serverUrl;
    _disposed = false;
    _openSocket();
  }

  void _openSocket() {
    if (_disposed || _serverUrl == null) return;
    _cleanupChannel();

    try {
      final wsUrl = AppConstants.buildWsUrl(_serverUrl!);
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _sub = _channel!.stream.listen(
        (message) {
          try {
            final decoded = jsonDecode(message.toString());
            if (decoded is Map<String, dynamic> &&
                decoded['type'] == 'NEW_ACCESS_EVENT' &&
                decoded['data'] is Map<String, dynamic>) {
              final log = AccessLog.fromJson(decoded['data'] as Map<String, dynamic>);
              _eventController.add(log);
            }
          } catch (_) {}
        },
        onError: (_) => _scheduleReconnect(),
        onDone: () => _scheduleReconnect(),
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), _openSocket);
  }

  void _cleanupChannel() {
    _sub?.cancel();
    _sub = null;
    _channel?.sink.close();
    _channel = null;
  }

  void disconnect() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _cleanupChannel();
  }
}
