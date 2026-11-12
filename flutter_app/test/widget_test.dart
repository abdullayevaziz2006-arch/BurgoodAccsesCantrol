import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:burgood_access_control/main.dart';

void main() {
  testWidgets('BurgoodApp renders login screen when unauthenticated',
      (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(const BurgoodApp());
    await tester.pumpAndSettle();

    expect(find.text('Burgood Access Control'), findsOneWidget);
    expect(find.text('Kirish'), findsOneWidget);
  });
}
