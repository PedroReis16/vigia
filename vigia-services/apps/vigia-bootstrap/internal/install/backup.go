package install

import "os"

const backupDirName = "fall-detection.bak"

// BundleBackupDir returns the temporary backup path used during updates.
func BundleBackupDir(dataDir string) string {
	return AppDir(dataDir) + ".bak"
}

// BackupBundle renames fall-detection/ → fall-detection.bak/ atomically.
// No-op (nil) when no bundle is installed yet.
func BackupBundle(dataDir string) error {
	src := AppDir(dataDir)
	if _, err := os.Stat(src); os.IsNotExist(err) {
		return nil
	}
	dst := BundleBackupDir(dataDir)
	_ = os.RemoveAll(dst)
	return os.Rename(src, dst)
}

// RestoreBundle renames fall-detection.bak/ → fall-detection/ and rewrites install.json.
// No-op when no backup exists.
func RestoreBundle(dataDir string, prevState *State) error {
	src := BundleBackupDir(dataDir)
	if _, err := os.Stat(src); os.IsNotExist(err) {
		return nil
	}
	dst := AppDir(dataDir)
	_ = os.RemoveAll(dst)
	if err := os.Rename(src, dst); err != nil {
		return err
	}
	if prevState != nil {
		return SaveState(StatePath(dataDir), prevState)
	}
	return nil
}

// CleanupBackup removes the backup directory created by BackupBundle.
func CleanupBackup(dataDir string) {
	_ = os.RemoveAll(BundleBackupDir(dataDir))
}
