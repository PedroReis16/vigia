class UserProfile {
  const UserProfile({
    required this.id,
    required this.name,
    required this.firstName,
    required this.lastName,
    required this.email,
    required this.phone,
    this.pictureUrl,
    this.canDeleteAccount = true,
  });

  final String id;
  final String name;
  final String firstName;
  final String lastName;
  final String email;
  final String phone;
  final String? pictureUrl;
  final bool canDeleteAccount;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      firstName: json['firstName'] as String? ?? '',
      lastName: json['lastName'] as String? ?? '',
      email: json['email'] as String? ?? '',
      phone: json['phone'] as String? ?? '',
      pictureUrl: json['pictureUrl'] as String?,
      canDeleteAccount: json['canDeleteAccount'] as bool? ?? true,
    );
  }
}
