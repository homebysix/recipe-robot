# Recipe Robot Development Notes

Some scattered notes to assist in the design and development of Recipe Robot.

<!-- MarkdownTOC -->

- [Recipe Robot Development Notes](#recipe-robot-development-notes)
    - [Facts](#facts)
    - [Interesting examples and edge cases to use for testing:](#interesting-examples-and-edge-cases-to-use-for-testing)
    - [Content Types](#content-types)
    - [Sparkle feeds](#sparkle-feeds)

<!-- /MarkdownTOC -->

---

## Facts

These are the pieces of information we collect from app and recipe input in order to create the corresponding recipe types.

- __app_file__
    The filename of the application bundle, if it differs from app_name.

- __app_name__
    The name of the app, as determined by `CFBundleName` in the app's Info.plist file.

- __app_path__
    The path to the app. Used when overriding [AppStoreApp recipes](https://github.com/autopkg/nmcspadden-recipes/blob/master/AppStoreApp/AppStoreApp.check.recipe#L13-L14).

- __bitbucket_repo__
    For a BitBucket URL, this is the path to the specified project. (For example, the bitbucket_repo for the input URL `https://bitbucket.org/tperfitt/path-launcher` would be `tperfitt/path-launcher`.)

- __blocking_applications__
    An array of strings corresponding to the applications that should not be running in order to safely install this app. Necessary to specify when deploying a pkg installer via Munki.

- __bundle_id__
    The bundle identifier of the app, as determined by `CFBundleIdentifier` in the app's Info.plist file.

- __codesign_authorities__
    The "expected authorities" that must be present (and in specified order) for [CodeSignatureVerifier](https://github.com/autopkg/autopkg/wiki/Processor-CodeSignatureVerifier) to pass.

- __codesign_reqs__
    The "requirements" that must be met in order for [CodeSignatureVerifier](https://github.com/autopkg/autopkg/wiki/Processor-CodeSignatureVerifier) to pass.

- __codesign_status__
    If an app is signed with v2 enclosure, this is "signed". Otherwise, it's "unsigned".

- __codesign_input_filename__
    The filename of the pkg or app to be passed to CodeSignatureVerifier. If omitted, Recipe Robot assumes "%NAME%.app"

- __description__
    A brief and understandable description of what the app does. If the input URL is from GitHub, SourceForge, or BitBucket, the description is obtained from that service's API. Otherwise, the description is obtained by searching MacUpdate for the top result matching app_name.

- __developer__
    The name of the developer or organization that makes the app.

- __download_filename__
    The name of the file downloaded from a specified input URL. (For example, `AutoPkgr-1.3.2.dmg`.)

- __download_format__
    The format of the file downloaded from a specified input URL. (For example, `dmg`)

- __download_url__
    The URL that points to the latest version of the app. Used in download recipes by the URLDownloader processor.

- __github_repo__
    For a GitHub URL, this is the path to the specified project. (For example, the github_repo for the input URL `https://github.com/lindegroup/autopkgr` would be `lindegroup/autopkgr`.)

- __icon_path__
    The path to the icns file used to display the app's primary icon. If munki or jss recipes are selected, this file will be converted to a 300px by 300px png file and saved in the output folder along with the recipes.

- __inspections__
    An array of strings that act as a breadcrumb trail during fact-gathering and prevent us from covering the same ground twice. This increases the speed of Recipe Robot and prevents getting trapped in loops.

- __is_from_app_store__
    Is "true" if the app contains an _MASReceipt file, indicating it was downloaded from the App Store. This results in the creation of AppStoreApp overrides instead of standalone recipes.

- __pkgsign_status__
    Is "signed" if the pkg file is signed, "unsigned" otherwise.

- __sourceforge_id__
    For a SourceForge URL, this is the path to the specified project. (For example, the bitbucket_repo for the input URL `https://bitbucket.org/tperfitt/path-launcher` would be `tperfitt/path-launcher`.)

- __sparkle_feed__
    The URL to the Sparkle feed (appcast) of the app, often used to create a download recipe that leverages [SparkleUpdateInfoProvider](https://github.com/autopkg/autopkg/wiki/Processor-SparkleUpdateInfoProvider).

- __sparkle_provides_version__
    Is True if a usable version number was found in the Sparkle feed, is False otherwise.

- __use_asset_regex__
    Is True if a GitHub repo has been inspected and that repo has multiple file formats in its releases.

- __user-agent__
    If accessing a download URL or Sparkle feed fails using the standard Python user-agent, an alternative user-agent is attempted. If that attempt succeeds, the user-agent fact is set, which causes the corresponding `request_headers` to be used in the resulting recipe.

- __version_key__
    Most apps use `CFBundleShortVersionString` to indicate the version, but some use `CFBundleVersion`. The version_key fact indicates which to use for the purpose of building recipes.

---

## Interesting examples and edge cases to use for testing:

Basic example of a signed app in a dmg (works as of 2015-10-07):
```
recipe-robot --verbose https://www.dropbox.com/s/0s2a66jrstvd594/AutoPkgr.dmg?dl=1
```

Basic example of a signed app in a pkg (works as of 2018-03-21):
```
recipe-robot --verbose https://www.dropbox.com/s/j9p1wqhecltxt5o/AutoPkgr-1.4.2.pkg?dl=1
```

Basic example of a signed app in a zip (works as of 2015-10-07):
```
recipe-robot --verbose https://www.dropbox.com/s/482p3tai0v8uvky/signed-app-in-zip.zip?dl=1
```

Basic example of an unsigned app in a dmg (works as of 2015-10-07):
```
recipe-robot --verbose https://www.dropbox.com/s/g7wke2p32ejibtt/unsigned-app-in-dmg.dmg?dl=1
```

Basic example of an unsigned app in a pkg (works as of 2015-10-07):
```
recipe-robot --verbose https://www.dropbox.com/s/6pawuykelhdvwq3/unsigned-app-in-pkg.pkg?dl=1
```

Basic example of an unsigned app in a zip (works as of 2015-10-07):
```
recipe-robot --verbose https://www.dropbox.com/s/uyhkiir6jpm0t79/unsigned-app-in-zip.zip?dl=1
```

Zip download reveals an installer in .app format:
```
recipe-robot --verbose http://download.bjango.com/skalacolor/
```

Signed installer download:
```
recipe-robot --verbose https://api.vivi.io/mac-pkg
```

Sparkle feed blocks Python user-agent:
```
recipe-robot --verbose https://download.sketchapp.com/sketch.zip
```

Downloaded disk image requires agreement to license before mounting:
```
recipe-robot --verbose https://www.revisionsapp.com/downloads/revisions-2.1.1.dmg
```

Sparkle feed lists the most recent items last, instead of first:
```
recipe-robot --verbose http://www.marinersoftware.com/sparkle/MacGourmet4/macgourmet4.xml
```

Dmg download reveals a pkg installer (and an uninstaller too):
```
recipe-robot --verbose http://downloads.econtechnologies.com/CS4_Download.dmg
```

Dmg download reveals a pkg installer, which contains an app:
```
recipe-robot --verbose https://pqrs.org/osx/karabiner/files/Karabiner-10.9.0.dmg
recipe-robot --verbose https://github.com/integralpro/nosleep/releases
```

App that uses a version 1 (obsolete) code signature:
```
recipe-robot --verbose http://mrrsoftware.com/Downloads/NameChanger/Updates/NameChanger-2_3_3.zip
```

App that uses a LooseVersion (3.1.4.0) for CFBundleShortVersionString (also, specifies download format in URL parameters):
```
recipe-robot --verbose https://srv3.airdroid.com/p14/web/getbinaryredirect?type=dmg
```

Direct download doesn't work because of "SSLV3_ALERT_HANDSHAKE_FAILURE":
```
recipe-robot --verbose http://www.macroplant.com/latest-binaries/adapter-mac.dmg
recipe-robot --verbose http://cdn.macroplant.com/release/Adapter-2.1.6.dmg
recipe-robot --verbose http://www.macroplant.com/adapter/adapterAppcast.xml
```

The app we want is not at the root level of the downloaded file:
```
recipe-robot --verbose https://github.com/jbtule/cdto/releases/download/2_6_0/cdto_2_6.zip
recipe-robot --verbose http://www.softobe.com/download/kinemac.dmg
recipe-robot --verbose http://www.softobe.com/download/flsy.dmg
```

Download URL has `&` which doesn't parse in Terminal:
```
recipe-robot --verbose http://www.dejal.com/download/?prod=simon&vers=4.1&lang=en&op=getnow&ref=footer
```

The download produces a `CERTIFICATE_VERIFY_FAILED` error:
```
recipe-robot --verbose https://updates.aviatorbrowser.com/Aviator.dmg
```

Direct download URL (dmg) is a different format than the Sparkle download URL (zip):
```
recipe-robot --verbose https://tunnelblick.net/release/Tunnelblick_3.7.8_build_5180.dmg
```

An app installer at the root level of the DMG (Can we have some kind of warning about this?):
```
recipe-robot --verbose http://cdn01.downloads.smartbear.com/soapui/5.2.0/SoapUI-5.2.0.dmg
```

Sparkle feed points to a 404 download URL, but based on the URL we should be able to build recipes anyway. (Assume it's an unsigned zip.)
```
recipe-robot --verbose /Applications/Screens.app
```

SUFeedURL is "NULL":
```
recipe-robot --verbose http://www.git-tower.com/download
```

A prefpane within a dmg:
```
recipe-robot --verbose https://bahoom.com/hyperdock/HyperDock.dmg
```

## Content Types

To get an grasp of the typical content types that Recipe Robot will be dealing with, I ran `curl -sIL` on every SPARKLE_FEED_URL and DOWNLOAD_URL in the homebysix-recipes repo. Here are the content types that were returned:

| Type                                | Count |
| ----------------------------------- | ----- |
| text/html                           | 101   |
| application/xml                     | 62    |
| application/zip                     | 33    |
| application/x-apple-diskimage       | 24    |
| text/xml                            | 24    |
| application/octet-stream            | 22    |
| text/plain                          | 7     |
| application/xhtml+xml               | 5     |
| application/rss+xml                 | 3     |
| binary/octet-stream                 | 3     |
| application/vnd.apple.installer+xml | 1     |
| application/x-bzip2                 | 1     |
| application/x-rss+xml               | 1     |
| plain/text                          | 1     |

("text/html" also includes error messages caused by input variables in URL.)

## Sparkle feeds

Sparkle feed that has item versions but not enclosure versions:

```xml
<?xml version="1.0"?>
<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
  <channel>
    <title>Caffeine</title>
    <description>Most recent changes with links to updates.</description>
    <language>en</language>
    <item>
      <title>Version 1.4.3</title>
      <sparkle:version>21</sparkle:version>
      <sparkle:shortVersionString>1.4.3</sparkle:shortVersionString>
      <pubDate>Sun, 14 April 2024 8:00:00 +0000</pubDate>
      <enclosure url="https://dr-caffeine-mac.s3.amazonaws.com/Caffeine_1.4.3.zip" length="5961295" type="application/octet-stream" sparkle:edSignature="985QTq5gW2CIAWdBTJqg1n8+5KTVGln5fIumSyCY+YI1CGSUx2InGSBdUWWih0j9XowDeXIIbyDyHqzdeDYNDw=="/>
      <sparkle:minimumSystemVersion>11.0</sparkle:minimumSystemVersion>
      <description><![CDATA[ <ul> <li>Added Sparkle updater</li> </ul> ]]></description>
    </item>
  </channel>
</rss>
```

Sparkle feed that has enclosure versions but not item versions:

```xml
<?xml version="1.0"?>
<rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" xmlns:dc="http://purl.org/dc/elements/1.1/" version="2.0">
  <channel>
    <title>coconutBattery changelog</title>
    <link>https://www.coconut-flavour.com/updates/coconutBattery.xml</link>
    <description>coconutBattery changelog</description>
    <language>en</language>
    <item>
      <title>Version 4.0.1</title>
      <description><![CDATA[ <body style="font: 12px '-apple-system', system-ui, BlinkMacSystemFont, segoe ui, Roboto, helvetica neue, Arial, sans-serif; line-height: 1.3; margin: 0; padding: 0; background: #fff; color: #000;"> <div style="background-color: #4c84b3; color: white; width: 80%; margin: 0 auto; padding: 10px; padding-left:20px; padding-right:20px; margin-top: 15px; text-align: center; border-radius: 8px;"> <b>All coconutBattery 3 Plus licenses were upgraded to coconutBattery 4 Plus Lifetime licenses.</b><br> <span style="display: block; margin-top: 10px;"> <b><a style="color: white; text-decoration: underline;" href="https://www.coconut-flavour.com/coconutBattery/#plus">- coconutBattery 4 Plus -</a></b> </span> </div> <div class="release" style="padding-left: 30px;padding-top:10px;"> <h2 style="font-size: 18px; font-weight: 600; margin-bottom: 10px;"><b>coconutBattery 4.0.1</b> <span style="opacity: 0.5;font-size:12px">| Dec 20, 2024</span></h2> <ul style="padding-left: 16px; margin: 0; list-style: disc;"> <li style="margin-bottom: 5px;">Fixed a bug that could cause displaying "NaN" in the history viewer for history that was imported from version 3</li> <li style="margin-bottom: 5px;">Info text if battery is not supported by lifetime viewer</li> <li style="margin-bottom: 5px;">If multiple adapters are connected, the one with the highest wattage is displayed</li> <li style="margin-bottom: 5px;">Print template selection now recognize Plus license correctly</li> <li style="margin-bottom: 5px;">Fixed display issues on iMac M3</li> <li style="margin-bottom: 5px;">The History Viewer "Save now" option shows matching icons for the device that will be saved </li> <li style="margin-bottom: 5px;">Fixed a bug where some coconutBattery 3 Plus licenses were not recognized correctly in coconutBattery 4</li> <li style="margin-bottom: 5px;">Added an option in the app settings to manually enable the coconutBattery menu bar</li> <li style="margin-bottom: 5px;">History Viewer now automatically selects first device when opened</li> <li style="margin-bottom: 5px;">History elements can be deleted using the context menu in the History Viewer</li> <li style="margin-bottom: 5px;">Toolbar state is now saved</li> <li style="margin-bottom: 5px;">Fixed battery manufacturer reading on some Macs</li> <li style="margin-bottom: 5px;">Battery health >100% is now displayed as 100% in non raw data mode</li> <li style="margin-bottom: 5px;">Fixed a bug that could cause the app displaying incorrectlry the charging state on Intel Macs </li> </ul> </div> <div class="release" style="padding-left: 30px;padding-top:10px;"> <h2 style="font-size: 18px; font-weight: 600; margin-bottom: 10px;"><b>coconutBattery 4.0.0</b> <span style="opacity: 0.5;font-size:12px">| Nov 30, 2024</span></h2> <ul style="padding-left: 16px; margin: 0; list-style: disc;"> <li style="margin-bottom: 5px;">Refined UI for improved usability</li> <li style="margin-bottom: 5px;">New App Icon</li> <li style="margin-bottom: 5px;">Realtime battery usage metrics for Macs</li> <li style="margin-bottom: 5px;">Improved device details viewer</li> <li style="margin-bottom: 5px;">Battery lifetime viewer now available for Macs</li> <li style="margin-bottom: 5px;">Re-engineered menu bar interface</li> <li style="margin-bottom: 5px;">Implemented low battery notifications for iPhones and iPads</li> </ul> </div> </body> ]]></description>
      <enclosure url="https://www.coconut-flavour.com/downloads/coconutBattery_401_130.zip" sparkle:version="4.0.1" sparkle:dsaSignature="MC0CFDiiAP1h+TJLfE+bDSe39osBfD5hAhUAlk2Iefd0mx6zTFPrqChwYai1dbE=" length="5457536" type="application/octet-stream"/>
      <sparkle:minimumSystemVersion>12.4</sparkle:minimumSystemVersion>
    </item>
    <item>
      <title>Version 3.9.18</title>
      <enclosure url="https://www.coconut-flavour.com/downloads/coconutBattery_3918_8BC5B481.zip" sparkle:version="3.9.18" sparkle:dsaSignature="MC4CFQCsOPpjH69d6Z2fVKWhDhlu2CgyywIVAKx5LGVSX9r6t6vUAY70wHS1DceW" length="14058872" type="application/octet-stream"/>
      <sparkle:minimumSystemVersion>10.11.0</sparkle:minimumSystemVersion>
    </item>
  </channel>
</rss>
```
