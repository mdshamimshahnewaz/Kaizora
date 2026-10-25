> বর্তমান পূর্ণ নির্দেশিকা: [User guide](user-guide/README.md), browser-এ `/user-guide/#roles`।

# Organization, member ও role ব্যবহারের নিয়ম

প্রথমে existing Django account থাকতে হবে। Public signup/email invitation এই scope-এ নেই।
Django Admin থেকে user account এবং অনুমতি অনুযায়ী business role ও membership manage করা যাবে।

## প্রথম organization — UI বা Admin

**App:** operator/superuser হিসেবে login → **Organizations → Create organization**।
Organization name, timezone ও existing owner username দিয়ে Create করুন। নিজের admin
account-কে owner করতে চাইলে Owner username-এ নিজের username দিন।

**Django Admin:** `/admin/` → **Organizations → Add**। একই তথ্য দিয়ে Save করুন।
নতুন user লাগলে আগে **Identity → Users → Add** থেকে account তৈরি করুন।

CLI ব্যবহার বাধ্যতামূলক নয়। Actor-এর active superuser অথবা
`organizations.bootstrap_organization` permission লাগবে। Owner হবে active existing user।
Operator ও owner আলাদা হলে operator স্বয়ংক্রিয় membership পাবেন না।

## Django Admin থেকে member/role management

Admin-এ ঢুকতে `is_staff` লাগবে; organization-এর কাজ করার জন্য owner বা সংশ্লিষ্ট
business permission-ও লাগবে। Organization তৈরি করে নিজের account-কে owner দিলে
সেই organization-এর management menu পাওয়া যাবে।

- **Organizations → Memberships → Add:** organization এবং existing username দিন।
- Membership খুলে status ও reason দিয়ে suspend/end/reactivate করুন।
- **Identity → Organization roles → Add:** organization, name, scope ও permissions দিন।
- Role খুলে permissions/status পরিবর্তন করুন; reason আবশ্যক।
- **Identity → Role assignments → Add:** একই organization-এর member ও role বেছে reason দিন।
- Assignment খুলে reason দিয়ে Save করলে revoke হবে; historical row থাকবে।
- Organization খুললে ownership-transfer form পাওয়া যাবে। Target member ও reason দিন।
- Audit events এবং raw Role Permission rows read-only থাকবে; role editor দিয়েই permissions বদলাবেন।

## App থেকে ব্যবহার

1. Owner login করে **Organizations → Open organization** যান।
2. **Members**-এ existing account-এর exact username দিয়ে **Add member** করুন।
3. **Roles → Create role** থেকে name ও permissions দিন অথবা preset নিন। Save করুন।
4. **Role assignments → Assign role** থেকে member/role বেছে reason লিখে confirm করুন।
   List বড় হলে Members ও Roles-এর page পাল্টে target-গুলো আগে দেখিয়ে নিন।
5. Role edit/archive ও assignment revoke করলে পরের request থেকেই access বদলাবে।
6. Member suspend/end করলে history থাকবে। Reactivate করলে একই membership ID ফেরত আসে;
   আগে revoke না করা live role আবার কার্যকর হয়।
7. Ownership transfer শুধু active owner করতে পারবেন। Target active member হতে হবে;
   confirm করার পর নিজের owner ক্ষমতা হারাবেন, তবে assigned custom roles থাকলে সেগুলো থাকবে।

## কে কী দেখতে পারে

| Actor | Access |
| --- | --- |
| Membership ছাড়া user | নিজের account; কোনো organization data নয় |
| Active basic member | Organization identity ও নিজের access summary |
| Owner | Organization member/role management এবং reserved ownership transfer |
| Custom role holder | কেবল assigned capability; roles additive |
| Django staff/superuser | Operator permission অনুযায়ী provisioning; membership ছাড়া tenant access নয় |

Member directory: `memberships.read`; add/status change: `memberships.manage`।
Role list/history: `roles.read`; role create/edit: `roles.manage`; assign/revoke: `roles.assign`।
Assignment UI-এর picker-এর জন্য member ও role read permissions-ও লাগে। Non-owner নিজের
বর্তমান permissions-এর বাইরে ক্ষমতা দিতে বা বেশি ক্ষমতার role edit/revoke করতে পারেন না।
Owner membership-এর status non-owner manager বদলাতে পারবেন না।

Role presets শুধু templates; কাউকে auto-assign হয় না। Project roles তৈরি করে রাখা যায়,
এবং project-specific assignment ও actual project checks `0008`-এ implement হয়েছে।
বর্তমান permission catalog-এ ভবিষ্যৎ module-এর key থাকা মানে সেই module implement হয়ে গেছে নয়।

Conflict বা network error হলে app authoritative state reload করে; নিজে থেকে write retry করে না।
Latest state দেখে তারপর আবার চেষ্টা করুন। নতুন environment-এ প্রথমে migrations চালান:

```bash
python backend/manage.py migrate
```

Local migration প্রয়োগ করা হয়েছে। Development server নিজে আগের মতো চালাবেন।
