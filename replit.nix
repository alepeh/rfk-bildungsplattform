{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.graphviz
    pkgs.pkg-config
    pkgs.coreutils
    pkgs.postgresql_15
  ];
}