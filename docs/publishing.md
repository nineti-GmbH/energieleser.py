# Publishing

Releases are tag-driven and published to PyPI via GitHub Actions Trusted Publishing.

1. Bump `version` in `pyproject.toml`.
2. Update the changelog (if present) and commit.
3. Tag and push:

   ```shell
   git tag v0.1.0
   git push --tags
   ```

4. The `.github/workflows/release.yml` workflow builds the sdist and wheel with `poetry build` and publishes them to PyPI.
5. Verify the release with a clean install:

   ```shell
   pip install energieleser==0.1.0
   ```
