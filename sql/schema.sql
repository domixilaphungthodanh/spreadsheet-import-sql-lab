CREATE TABLE IF NOT EXISTS tickets (
    ticket_code TEXT NOT NULL UNIQUE CHECK(length(ticket_code)=6 AND ticket_code GLOB 'SC-[0-9][0-9][0-9]'),
    service TEXT NOT NULL CHECK(length(trim(service))>0),
    received_on TEXT NOT NULL CHECK(date(received_on,'+0 days') IS received_on),
    status TEXT NOT NULL CHECK(status IN ('pending','in_progress','completed'))
) STRICT;
