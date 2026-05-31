package install

import (
	"os"
	"path/filepath"
	"testing"
)

func TestBackupBundle_noBundle(t *testing.T) {
	dir := t.TempDir()
	// No fall-detection/ present — BackupBundle should be a no-op.
	if err := BackupBundle(dir); err != nil {
		t.Fatalf("BackupBundle on empty dir: %v", err)
	}
	if _, err := os.Stat(BundleBackupDir(dir)); !os.IsNotExist(err) {
		t.Fatal("expected no backup dir when source is absent")
	}
}

func TestBackupBundle_renamesBundle(t *testing.T) {
	dir := t.TempDir()
	appDir := AppDir(dir)
	bin := filepath.Join(appDir, bundleBinaryName)
	if err := os.MkdirAll(appDir, 0o750); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(bin, []byte("bin"), 0o750); err != nil {
		t.Fatal(err)
	}

	if err := BackupBundle(dir); err != nil {
		t.Fatalf("BackupBundle: %v", err)
	}

	// Original should be gone, backup should exist.
	if _, err := os.Stat(appDir); !os.IsNotExist(err) {
		t.Fatal("expected AppDir to be renamed away")
	}
	backupBin := filepath.Join(BundleBackupDir(dir), bundleBinaryName)
	if _, err := os.Stat(backupBin); err != nil {
		t.Fatalf("backup binary missing: %v", err)
	}
}

func TestRestoreBundle_noBackup(t *testing.T) {
	dir := t.TempDir()
	// No backup — RestoreBundle should be a no-op.
	if err := RestoreBundle(dir, nil); err != nil {
		t.Fatalf("RestoreBundle with no backup: %v", err)
	}
}

func TestRestoreBundle_restoresFromBackup(t *testing.T) {
	dir := t.TempDir()
	appDir := AppDir(dir)

	// Simulate failed install: backup exists, app dir does not.
	backupDir := BundleBackupDir(dir)
	backupBin := filepath.Join(backupDir, bundleBinaryName)
	if err := os.MkdirAll(backupDir, 0o750); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(backupBin, []byte("old-bin"), 0o750); err != nil {
		t.Fatal(err)
	}

	prevState := &State{Version: "1.0.0", BinaryPath: filepath.Join(appDir, bundleBinaryName)}
	if err := RestoreBundle(dir, prevState); err != nil {
		t.Fatalf("RestoreBundle: %v", err)
	}

	// Backup should be gone, app dir restored.
	if _, err := os.Stat(backupDir); !os.IsNotExist(err) {
		t.Fatal("expected backup dir to be removed after restore")
	}
	if _, err := os.Stat(filepath.Join(appDir, bundleBinaryName)); err != nil {
		t.Fatalf("restored binary missing: %v", err)
	}

	// install.json should be written.
	st, err := LoadState(StatePath(dir))
	if err != nil || st == nil || st.Version != "1.0.0" {
		t.Fatalf("state after restore: %+v err %v", st, err)
	}
}

func TestCleanupBackup_removesDir(t *testing.T) {
	dir := t.TempDir()
	backupDir := BundleBackupDir(dir)
	if err := os.MkdirAll(backupDir, 0o750); err != nil {
		t.Fatal(err)
	}
	CleanupBackup(dir)
	if _, err := os.Stat(backupDir); !os.IsNotExist(err) {
		t.Fatal("expected backup dir removed")
	}
}

func TestCleanupBackup_noOpWhenAbsent(t *testing.T) {
	dir := t.TempDir()
	// Should not panic or error.
	CleanupBackup(dir)
}
