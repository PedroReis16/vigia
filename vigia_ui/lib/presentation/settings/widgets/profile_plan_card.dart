import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/plan/plan_view.dart';
import 'package:vigia_ui/domain/plan/user_plan.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';

class ProfilePlanCard extends StatelessWidget {
  const ProfilePlanCard({super.key});

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final plan = mockUserPlan();
    final view = buildPlanView(
      plan,
      plan.currentPackageId,
      planLocale(Localizations.localeOf(context).languageCode),
    );

    return Column(
      key: const Key('profile-plan'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(t.planTitle, style: theme.textTheme.titleLarge),
        const SizedBox(height: 4),
        Text(t.planPreviewHint, style: theme.textTheme.bodySmall),
        const SizedBox(height: 12),
        Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(t.planActive, style: theme.textTheme.titleMedium),
                const SizedBox(height: 16),
                Text(
                  _packageName(t, view.packageId),
                  key: const Key('profile-plan-name'),
                  style: theme.textTheme.titleLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  t.planRenews(view.renewalLabel),
                  style: theme.textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerLeft,
                  child: _pill(t.planStatusActive, _PillTone.active),
                ),
                const SizedBox(height: 8),
                Text.rich(
                  TextSpan(
                    text: view.priceLabel,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                    children: [
                      TextSpan(
                        text: ' ${t.planPerMonth}',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                  key: const Key('profile-plan-price'),
                ),
                const SizedBox(height: 20),
                for (final usage in view.usages) ...[
                  Text(_usageLabel(t, usage), style: theme.textTheme.bodySmall),
                  const SizedBox(height: 6),
                  _meter(theme, usage, _usageLabel(t, usage)),
                  const SizedBox(height: 16),
                ],
                for (final feature in view.features)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.check,
                          size: 18,
                          color: Color(0xFF166534),
                        ),
                        const SizedBox(width: 8),
                        Expanded(child: Text(_featureLabel(t, feature))),
                      ],
                    ),
                  ),
                const SizedBox(height: 8),
                _group(
                  theme,
                  title: t.planPaymentMethod,
                  child: Row(
                    children: [
                      Icon(Icons.credit_card, color: theme.colorScheme.primary),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              view.cardLabel,
                              key: const Key('profile-plan-card'),
                              style: theme.textTheme.titleSmall,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              t.planExpires(view.expiryLabel),
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                _group(
                  theme,
                  title: t.planPayments,
                  child: Column(
                    children: [
                      for (var i = 0; i < view.invoices.length; i++) ...[
                        if (i > 0)
                          Divider(
                            height: 1,
                            color: theme.colorScheme.outlineVariant,
                          ),
                        _invoice(theme, t, view.invoices[i]),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _meter(ThemeData theme, PlanUsageView usage, String label) {
    final fill = usage.overLimit
        ? theme.colorScheme.error
        : theme.colorScheme.primary;
    return Semantics(
      label: label,
      child: ClipRRect(
        borderRadius: BorderRadius.circular(99),
        child: SizedBox(
          height: 6,
          child: Stack(
            fit: StackFit.expand,
            children: [
              ColoredBox(color: theme.colorScheme.outlineVariant),
              FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: usage.percent / 100,
                child: ColoredBox(color: fill),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _group(
    ThemeData theme, {
    required String title,
    required Widget child,
  }) {
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Divider(height: 1, color: theme.colorScheme.outlineVariant),
          const SizedBox(height: 16),
          Text(title, style: theme.textTheme.titleSmall),
          const SizedBox(height: 12),
          child,
        ],
      ),
    );
  }

  Widget _invoice(
    ThemeData theme,
    AppLocalizations t,
    PlanInvoiceView invoice,
  ) {
    final paid = invoice.status == 'paid';
    return Padding(
      key: ValueKey('profile-plan-invoice-${invoice.id}'),
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(invoice.dateLabel, style: theme.textTheme.titleSmall),
                const SizedBox(height: 2),
                Text(
                  _packageName(t, invoice.packageId),
                  style: theme.textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(invoice.amountLabel, style: theme.textTheme.titleSmall),
              const SizedBox(height: 4),
              _pill(
                paid ? t.planInvoicePaid : t.planInvoiceScheduled,
                paid ? _PillTone.paid : _PillTone.scheduled,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _pill(String label, _PillTone tone) {
    final (background, foreground) = switch (tone) {
      _PillTone.active ||
      _PillTone.paid => (const Color(0x1F16A34A), const Color(0xFF166534)),
      _PillTone.scheduled => (const Color(0x29669CEE), const Color(0xFF1D4E89)),
    };
    return DecoratedBox(
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(99),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
        child: Text(
          label,
          style: TextStyle(
            color: foreground,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  String _usageLabel(AppLocalizations t, PlanUsageView usage) {
    if (usage.id == 'storage') {
      return t.planUsageStorage(usage.usedLabel, usage.limitLabel);
    }
    return t.planUsageDevices(usage.usedLabel, usage.limitLabel);
  }

  String _featureLabel(AppLocalizations t, PlanFeatureView feature) {
    return switch (feature.key) {
      PlanFeatureKey.device => t.planFeatureDevice,
      PlanFeatureKey.devices => t.planFeatureDevices(feature.count ?? 0),
      PlanFeatureKey.history => t.planFeatureHistory(feature.days ?? 0),
      PlanFeatureKey.storage => t.planFeatureStorage(feature.gb ?? 0),
      PlanFeatureKey.alerts => t.planFeatureAlerts,
      PlanFeatureKey.clips => t.planFeatureClips,
      PlanFeatureKey.priority => t.planFeaturePriority,
    };
  }

  String _packageName(AppLocalizations t, String id) {
    return switch (id) {
      'essential' => t.planEssential,
      'home' => t.planHome,
      _ => t.planFamily,
    };
  }
}

enum _PillTone { active, paid, scheduled }
