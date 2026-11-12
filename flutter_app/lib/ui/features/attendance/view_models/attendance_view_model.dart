import 'package:flutter/foundation.dart';
import 'package:intl/intl.dart';
import '../../../../data/models/access_log.dart';
import '../../../../data/repositories/access_repository.dart';

class AttendanceViewModel extends ChangeNotifier {
  AttendanceViewModel({required AccessRepository accessRepository}) : _repo = accessRepository;

  final AccessRepository _repo;

  List<AccessLog> _logs = [];
  List<AccessLog> get logs => _logs;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  String? _directionFilter;
  String? get directionFilter => _directionFilter;

  DateTime _selectedDate = DateTime.now();
  DateTime get selectedDate => _selectedDate;

  String _searchQuery = '';
  String get searchQuery => _searchQuery;

  void setDirectionFilter(String? dir) {
    _directionFilter = dir;
    loadLogs();
  }

  void setDate(DateTime date) {
    _selectedDate = date;
    loadLogs();
  }

  void setSearch(String q) {
    _searchQuery = q;
    notifyListeners();
  }

  List<AccessLog> get visibleLogs {
    if (_searchQuery.trim().isEmpty) return _logs;
    final q = _searchQuery.trim().toLowerCase();
    return _logs.where((l) {
      return (l.userName?.toLowerCase().contains(q) ?? false) ||
          (l.employeeNo?.toLowerCase().contains(q) ?? false);
    }).toList();
  }

  Future<void> loadLogs({int? onlyUserId}) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final dateStr = DateFormat('yyyy-MM-dd').format(_selectedDate);
      _logs = await _repo.getLogs(
        limit: 150,
        direction: _directionFilter,
        startDate: dateStr,
        endDate: dateStr,
        userId: onlyUserId,
      );
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
