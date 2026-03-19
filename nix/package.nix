{ pkgs ? import <nixpkgs> {} }:

let
  python3 = pkgs.python3;
  pythonPackages = python3.pkgs;
in

pythonPackages.buildPythonApplication rec {
  pname = "qutebrowser-yubiqt";
  version = "3.6.3+yubiqt";
  format = "setuptools";

  src = ./..;

  nativeBuildInputs = with pkgs; [
    qt6.wrapQtAppsHook
  ];

  buildInputs = with pkgs; [
    qt6.qtbase
    qt6.qtwebengine
  ];

  propagatedBuildInputs = with pythonPackages; [
    pyqt6
    pyqt6-webengine
    jinja2
    pyyaml
    pygments
    adblock
  ];

  # Tests require a display and network access
  doCheck = false;

  dontWrapQtApps = true;

  postFixup = ''
    wrapQtApp "$out/bin/qutebrowser" \
      --prefix PATH : ${pkgs.lib.makeBinPath (with pkgs; [ qt6.qtwebengine ])}
  '';

  meta = with pkgs.lib; {
    description = "Keyboard-driven browser with FIDO2/WebAuthn YubiKey support";
    homepage = "https://github.com/Jesssullivan/qutebrowser";
    license = licenses.gpl3Plus;
    maintainers = [];
    mainProgram = "qutebrowser";
    platforms = platforms.unix;
  };
}
