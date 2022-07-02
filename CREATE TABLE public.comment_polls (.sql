CREATE TABLE public.submission_options (
	id integer PRIMARY KEY,
    submission_id integer NOT NULL,
    body_html character varying(500) NOT NULL,
	exclusive boolean NOT NULL
);

CREATE INDEX option_submission ON public.submission_options USING btree (submission_id);

ALTER TABLE ONLY public.submission_options
    ADD CONSTRAINT option_submission_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) MATCH FULL;



CREATE SEQUENCE public.submission_option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY public.submission_options ALTER COLUMN id SET DEFAULT nextval('public.submission_option_id_seq'::regclass);



CREATE TABLE public.submission_option_votes (
	option_id integer NOT NULL,
    user_id integer NOT NULL,
    created_utc integer NOT NULL,
    submission_id integer,
);



ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT submission_option_votes_pkey PRIMARY KEY (option_id, user_id);


ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_option_fkey FOREIGN KEY (option_id) REFERENCES public.submission_options(id) MATCH FULL;

ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_user_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) MATCH FULL;

ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_submission_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) MATCH FULL;















CREATE TABLE public.submission_options (
	id integer PRIMARY KEY,
    submission_id integer NOT NULL,
    body_html character varying(500) NOT NULL,
	exclusive boolean NOT NULL
);

CREATE INDEX option_submission ON public.submission_options USING btree (submission_id);

ALTER TABLE ONLY public.submission_options
    ADD CONSTRAINT option_submission_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) MATCH FULL;



CREATE SEQUENCE public.submission_option_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY public.submission_options ALTER COLUMN id SET DEFAULT nextval('public.submission_option_id_seq'::regclass);



CREATE TABLE public.submission_option_votes (
	option_id integer NOT NULL,
    user_id integer NOT NULL,
    created_utc integer NOT NULL,
    submission_id integer,
);



ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT submission_option_votes_pkey PRIMARY KEY (option_id, user_id);


ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_option_fkey FOREIGN KEY (option_id) REFERENCES public.submission_options(id) MATCH FULL;

ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_user_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) MATCH FULL;

ALTER TABLE ONLY public.submission_option_votes
    ADD CONSTRAINT vote_submission_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) MATCH FULL;