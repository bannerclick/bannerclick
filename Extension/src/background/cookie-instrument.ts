import { incrementedEventOrdinal } from "../lib/extension-session-event-ordinal";
import { extensionSessionUuid } from "../lib/extension-session-uuid";
import { boolToInt, escapeString } from "../lib/string-utils";
import { JavascriptCookie, JavascriptCookieRecord } from "../schema";

import Cookie = browser.cookies.Cookie;
import OnChangedCause = browser.cookies.OnChangedCause;
import SameSiteStatus = browser.cookies.SameSiteStatus


// Convert '01-01-2028' to UNIX time (seconds since epoch)
const COOKIE_EXPIRY = new Date('2028-01-01T12:12:12Z').getTime() / 1000;


export const transformCookieObjectToMatchOpenWPMSchema = (cookie: Cookie) => {
  const javascriptCookie = {} as JavascriptCookie;

  // Expiry time (in seconds)
  // May return ~Max(int64). I believe this is a session
  // cookie which doesn't expire. Sessions cookies with
  // non-max expiry time expire after session or at expiry.
  const expiryTime = cookie.expirationDate; // returns seconds
  let expiryTimeStringOriginal;
  const maxInt64 = 9223372036854776000;
  if (!cookie.expirationDate || expiryTime === maxInt64) {
    expiryTimeStringOriginal = "9999-12-31T21:59:59.000Z";
  } else {
    const expiryTimeDate = new Date(expiryTime * 1000); // requires milliseconds
    expiryTimeStringOriginal = expiryTimeDate.toISOString();
  }

  // TODO: Added for 01-01-2028 Expiry Time
  const expiryTimeString = new Date(COOKIE_EXPIRY * 1000).toISOString(); // requires milliseconds

  javascriptCookie.expiry = expiryTimeString;
  javascriptCookie.original_expiry = expiryTimeStringOriginal;

  javascriptCookie.is_http_only = boolToInt(cookie.httpOnly);
  javascriptCookie.is_host_only = boolToInt(cookie.hostOnly);

  // in Database is_session is stored correctly, but in cookie jar changes to normal with expiry date of 01-01-2028
  javascriptCookie.is_session = boolToInt(cookie.session);

  javascriptCookie.host = escapeString(cookie.domain);
  javascriptCookie.is_secure = boolToInt(cookie.secure);
  javascriptCookie.name = escapeString(cookie.name);
  javascriptCookie.path = escapeString(cookie.path);
  javascriptCookie.value = escapeString(cookie.value);
  javascriptCookie.same_site = escapeString(cookie.sameSite);
  javascriptCookie.first_party_domain = escapeString(cookie.firstPartyDomain);
  javascriptCookie.store_id = escapeString(cookie.storeId);

  javascriptCookie.time_stamp = new Date().toISOString();

  return javascriptCookie;
};

export const bcTransformCookieObjectToMatchOpenWPMSchema = (update2: JavascriptCookieRecord, cookieName: string) => {
  update2.name = escapeString(cookieName);
};

export class CookieInstrument {
  private readonly dataReceiver;
  private onChangedListener;

  constructor(dataReceiver) {
    this.dataReceiver = dataReceiver;
  }

  public run(crawlID) {
    // Instrument cookie changes
    this.onChangedListener = async (changeInfo: {
      /** True if a cookie was removed. */
      removed: boolean;
      /** Information about the cookie that was set or removed. */
      cookie: Cookie;
      /** The underlying reason behind the cookie's change. */
      cause: OnChangedCause;
    }) => {

      const Separator = '-_-';
      const end = 'bannerclick';

      if ( // TODO: cookies ADDED BY BC, no need for further processing
        ( // notifying extended cookies
          changeInfo.cause === 'overwrite' &&
          changeInfo.removed &&
          changeInfo.cookie.expirationDate &&
          changeInfo.cookie.expirationDate === COOKIE_EXPIRY
        )
        ||
        ( // notifying extended cookies
          changeInfo.cause === 'explicit' &&
          !changeInfo.removed &&
          changeInfo.cookie.expirationDate &&
          changeInfo.cookie.expirationDate === COOKIE_EXPIRY
        )
      ) {
        return;
      }

      const eventType = changeInfo.removed ? "deleted" : "added-or-changed";
      const update: JavascriptCookieRecord = {
        record_type: eventType,
        change_cause: changeInfo.cause,
        browser_id: crawlID,
        extension_session_uuid: extensionSessionUuid,
        event_ordinal: incrementedEventOrdinal(),
        ...transformCookieObjectToMatchOpenWPMSchema(changeInfo.cookie),
      };
      // visit_id, current_site added after saving record
      this.dataReceiver.saveRecord("javascript_cookies", update);

      // if update or visit_id not defined, don't process further
      if (!update || !update.visit_id)
        return

      // TODO: ADDED BY ME
      const cookieHost: string = update.host.startsWith('.') ? update.host.substring(1) : update.host;
      const currentTabUrl = update.current_site;
      const bcCookieName = escapeString(`${currentTabUrl}${Separator}${update.name}${Separator}${end}`)

      const update2: JavascriptCookieRecord = { ...update };
      bcTransformCookieObjectToMatchOpenWPMSchema(update2, bcCookieName);

      this.dataReceiver.saveRecord("javascript_cookies", update2);
      this.dataReceiver.saveRecord("bc_cookies", update2);
      // this.dataReceiver.logDebug(`MY DEBUG: inside Cookie Instrument Cookie Object: \n${JSON.stringify(update, null, 2)}`)
      // this.dataReceiver.logDebug(`MY DEBUG: inside Cookie Instrument Cookie Object2: \n${JSON.stringify(update2, null, 2)}`)

      const FQDN: string = `http${update.is_secure ? 's' : ''}://${cookieHost}${update.path}`;

      if (!changeInfo.removed) {
        await saveCookies(update, FQDN);
      } else if (changeInfo.removed && changeInfo.cause === 'expired') {
        await saveCookies(update, FQDN);
      }
    };
    browser.cookies.onChanged.addListener(this.onChangedListener);
  }

  public async saveAllCookies(crawlID) {
    const allCookies = await browser.cookies.getAll({});
    await Promise.all(
      allCookies.map((cookie: Cookie) => {
        const update: JavascriptCookieRecord = {
          record_type: "manual-export",
          browser_id: crawlID,
          extension_session_uuid: extensionSessionUuid,
          ...transformCookieObjectToMatchOpenWPMSchema(cookie),
        };
        return this.dataReceiver.saveRecord("javascript_cookies", update);
      }),
    );
  }

  public cleanup() {
    if (this.onChangedListener) {
      browser.cookies.onChanged.removeListener(this.onChangedListener);
    }
  }
}


async function saveCookies(update: JavascriptCookieRecord, FQDN: string) {

  const cookieSharedProperties = {
    url: FQDN,
    value: update.value,
    path: update.path,
    secure: Boolean(update.is_secure),
    httpOnly: Boolean(update.is_http_only),
    sameSite: update.same_site as SameSiteStatus,
    expirationDate: COOKIE_EXPIRY,
    storeId: update.store_id,
    firstPartyDomain: update.first_party_domain,
  };

  try {
    if (update.is_host_only) {
      await browser.cookies.set({
        ...cookieSharedProperties,
        name: update.name,
      });
    } else {
      const cookieSharedPropertiesWithDomain = {
        ...cookieSharedProperties,
        domain: update.host,
      }
      await browser.cookies.set({
        ...cookieSharedPropertiesWithDomain,
        name: update.name,
      });
    }
  } catch (error) {
    console.error(
      `Error saving cookie \n${JSON.stringify(update, null, 2)}\n${error}`
    )
  }
}

