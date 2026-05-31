// SPDX-FileCopyrightText: Copyright (C) 2023-2025 Bayerische Motoren Werke Aktiengesellschaft (BMW AG)<lichtblick@bmwgroup.com>
// SPDX-License-Identifier: MPL-2.0

// This Source Code Form is subject to the terms of the Mozilla Public
// License, v2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

import { useEffect } from "react";
import { createRoot } from "react-dom/client";

import Logger from "@lichtblick/log";
import type { IDataSourceFactory } from "@lichtblick/suite-base";
import CssBaseline from "@lichtblick/suite-base/components/CssBaseline";

import { CompatibilityBanner } from "./CompatibilityBanner";
import { canRenderApp } from "./canRenderApp";

const log = Logger.getLogger(__filename);

function LogAfterRender(props: React.PropsWithChildren): React.JSX.Element {
  useEffect(() => {
    // Integration tests look for this console log to indicate the app has rendered once
    // We use console.debug to bypass our logging library which hides some log levels in prod builds
    console.debug("App rendered");
    
    const loadLayoutFromUrl = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      let layoutParam = urlParams.get('layout');
      
      // If no layout parameter specified, default to Default.json
      if (!layoutParam) {
        layoutParam = "Default.json";
        log.info("No layout parameter specified, defaulting to Default.json");
      }

      try {
        const layoutUrl = `${window.location.origin}/assets/lichtblick_layouts/${layoutParam}`;
        const response = await fetch(layoutUrl);
        if (response.ok) {
          const layoutData = await response.json();
          
          if (!layoutData) {
            log.warn(`Layout data is empty for: ${layoutParam}`);
            return;
          }
          
          // Wait for app to be ready, then simulate the file input change that manual import uses
          setTimeout(() => {
            // Look for file input elements that might be used for layout import
            const fileInputs = document.querySelectorAll('input[type="file"]');
            
            if (fileInputs.length > 0) {
              const fileInput = fileInputs[0] as HTMLInputElement;
              
              // Create a mock File object
              const layoutString = JSON.stringify(layoutData) ?? "{}";
              const layoutBlob = new Blob([layoutString], { type: 'application/json' });
              const layoutFile = new File([layoutBlob], layoutParam!, { type: 'application/json' });
              
              // Create a mock FileList
              const mockFileList = {
                0: layoutFile,
                length: 1,
                item: (index: number) => index === 0 ? layoutFile : null,
                [Symbol.iterator]: function* () {
                  yield layoutFile;
                }
              };
              
              // Set the files and trigger change event
              Object.defineProperty(fileInput, 'files', {
                value: mockFileList,
                writable: false,
              });
              
              const changeEvent = new Event('change', { bubbles: true });
              fileInput.dispatchEvent(changeEvent);
              
              log.info(`Triggered layout import for: ${layoutParam}`);
            } else {
              // If no file input found, try again later
              setTimeout(loadLayoutFromUrl, 1000);
            }
          }, 3000);
          
          log.info(`Successfully fetched layout from URL: ${layoutParam}`);
        } else {
          // Layout file not found, use default behavior
          if (layoutParam === "Default.json") {
            log.info("Default.json not found, using default app behavior");
          } else {
            log.warn(`Layout file not found: ${layoutParam} (${response.status}), using default app behavior`);
          }
        }
      } catch (error) {
        if (layoutParam === "Default.json") {
          log.info(`Default.json could not be loaded: ${error}, using default app behavior`);
        } else {
          log.error(`Error loading layout ${layoutParam}: ${error}, using default app behavior`);
        }
      }
    };

    loadLayoutFromUrl();
  }, []);
  
  return <>{props.children}</>;
}

export type MainParams = {
  dataSources?: IDataSourceFactory[];
  extraProviders?: React.JSX.Element[];
  rootElement?: React.JSX.Element;
};

export async function main(getParams: () => Promise<MainParams> = async () => ({})): Promise<void> {
  log.debug("initializing");

  window.onerror = (...args) => {
    console.error(...args);
  };

  const rootEl = document.getElementById("root");
  if (!rootEl) {
    throw new Error("missing #root element");
  }

  const chromeMatch = navigator.userAgent.match(/Chrome\/(\d+)\./);
  const chromeVersion = chromeMatch ? parseInt(chromeMatch[1] ?? "", 10) : 0;
  const isChrome = chromeVersion !== 0;

  const canRender = canRenderApp();
  const banner = (
    <CompatibilityBanner
      isChrome={isChrome}
      currentVersion={chromeVersion}
      isDismissable={canRender}
    />
  );

  if (!canRender) {
    const root = createRoot(rootEl);
    root.render(
      <LogAfterRender>
        <CssBaseline>{banner}</CssBaseline>
      </LogAfterRender>,
    );
    return;
  }

  // Use an async import to delay loading the majority of suite-base code until the CompatibilityBanner
  // can be displayed.
  const { installDevtoolsFormatters, overwriteFetch, waitForFonts, initI18n, StudioApp } =
    await import("@lichtblick/suite-base");
  installDevtoolsFormatters();
  overwriteFetch();
  // consider moving waitForFonts into App to display an app loading screen
  await waitForFonts();
  await initI18n();

  const { WebRoot } = await import("./WebRoot");
  const params = await getParams();
  const rootElement = params.rootElement ?? (
    <WebRoot extraProviders={params.extraProviders} dataSources={params.dataSources}>
      <StudioApp />
    </WebRoot>
  );

  const root = createRoot(rootEl);
  root.render(
    <LogAfterRender>
      {banner}
      {rootElement}
    </LogAfterRender>,
  );
}
