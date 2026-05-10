package install

import (
	"archive/tar"
	"compress/gzip"
	"context"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const bundleDownloadSuffix = ".bundle-download.tar.gz.partial"

// InstallFallDetectionBundle downloads the PyInstaller onedir tarball from url into vigiaRoot,
// matching the manual deploy flow: extract → single top-level dir → rename to fall-detection → chmod vigia-fall-detection.
func InstallFallDetectionBundle(ctx context.Context, downloadURL, vigiaRoot string) error {
	if err := os.MkdirAll(vigiaRoot, 0o755); err != nil {
		return err
	}

	tmpArchive := filepath.Join(vigiaRoot, bundleDownloadSuffix)
	if err := downloadTarball(ctx, downloadURL, tmpArchive); err != nil {
		return fmt.Errorf("download: %w", err)
	}
	defer func() { _ = os.Remove(tmpArchive) }()

	staging, err := os.MkdirTemp(vigiaRoot, ".staging-")
	if err != nil {
		return err
	}
	defer func() { _ = os.RemoveAll(staging) }()

	if err := extractTarGz(tmpArchive, staging); err != nil {
		return fmt.Errorf("extract: %w", err)
	}
	if err := promoteStagingBundle(staging, vigiaRoot); err != nil {
		return fmt.Errorf("layout: %w", err)
	}

	bin := BinaryPath(vigiaRoot)
	if _, err := os.Stat(bin); err != nil {
		return fmt.Errorf("após extrair, executável não encontrado em %s: %w", bin, err)
	}
	if err := os.Chmod(bin, 0o755); err != nil {
		return err
	}
	return nil
}

func downloadTarball(ctx context.Context, downloadURL, destPath string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, downloadURL, nil)
	if err != nil {
		return err
	}

	client := &http.Client{Timeout: 45 * time.Minute}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("download failed: HTTP %d", resp.StatusCode)
	}

	tmp := destPath + ".tmp"
	f, err := os.OpenFile(tmp, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}

	if _, err := io.Copy(f, resp.Body); err != nil {
		f.Close()
		_ = os.Remove(tmp)
		return err
	}
	if err := f.Close(); err != nil {
		_ = os.Remove(tmp)
		return err
	}

	if err := os.Rename(tmp, destPath); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func extractTarGz(archivePath, destDir string) error {
	f, err := os.Open(archivePath)
	if err != nil {
		return err
	}
	defer f.Close()

	gzr, err := gzip.NewReader(f)
	if err != nil {
		return fmt.Errorf("gzip: %w", err)
	}
	defer gzr.Close()

	tr := tar.NewReader(gzr)

	absDest, err := filepath.Abs(destDir)
	if err != nil {
		return err
	}

	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}

		if hdr.Typeflag == tar.TypeXHeader || hdr.Typeflag == tar.TypeXGlobalHeader {
			continue
		}

		name := filepath.Clean(hdr.Name)
		if name == "." || strings.HasPrefix(name, "..") {
			return fmt.Errorf("nome inválido no arquivo: %q", hdr.Name)
		}

		target := filepath.Join(absDest, name)
		cleanTarget := filepath.Clean(target)
		sep := string(os.PathSeparator)
		if cleanTarget != absDest && !strings.HasPrefix(cleanTarget+sep, absDest+sep) {
			return fmt.Errorf("caminho ilegal no arquivo: %q", hdr.Name)
		}

		mode := hdr.FileInfo().Mode()

		switch hdr.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(cleanTarget, mode.Perm()); err != nil {
				return err
			}
		case tar.TypeReg, tar.TypeRegA:
			if err := os.MkdirAll(filepath.Dir(cleanTarget), 0o755); err != nil {
				return err
			}
			out, err := os.OpenFile(cleanTarget, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, mode.Perm()&0o777)
			if err != nil {
				return err
			}
			if _, err := io.CopyN(out, tr, hdr.Size); err != nil {
				out.Close()
				return err
			}
			if err := out.Close(); err != nil {
				return err
			}
		default:
			return fmt.Errorf("tipo de entrada não suportado no tarball (%c): %q", hdr.Typeflag, hdr.Name)
		}
	}
}

func promoteStagingBundle(stagingRoot, vigiaRoot string) error {
	entries, err := os.ReadDir(stagingRoot)
	if err != nil {
		return err
	}
	var dirs []os.DirEntry
	for _, e := range entries {
		if !e.IsDir() {
			return fmt.Errorf("tarball deve conter apenas um diretório no topo; encontrado ficheiro %q", e.Name())
		}
		dirs = append(dirs, e)
	}
	if len(dirs) != 1 {
		return fmt.Errorf("esperado exatamente um diretório no topo do tarball, obtido %d", len(dirs))
	}

	src := filepath.Join(stagingRoot, dirs[0].Name())
	dst := AppDir(vigiaRoot)
	if err := os.RemoveAll(dst); err != nil {
		return err
	}
	if err := os.Rename(src, dst); err != nil {
		return err
	}
	return nil
}
