library(dplyr)
library(car)
library(MASS)
library(readr)
library(pscl)
library(ggplot2)
library(jtools)
library(interplot)
library(stargazer)
library(Stack)
source("helpers.r")
library(texreg)
library(xtable)

projects.active = read_csv("projects_active.csv")
nrow(projects.active)

projects.active$newcomers_delta = projects.active$newcomers - projects.active$new_newcomers
projects.active$has_oldnew_contributors = projects.active$newcomers_delta > 0
projects.active$has_new_contributors = projects.active$newcomers > 0
projects.active$num_new_contributors = projects.active$newcomers
projects.active$has_newnew_contributors = projects.active$new_newcomers > 0
projects.active$num_newnew_contributors = projects.active$new_newcomers

projects.active$has_contrib = projects.active$contrib_bytes > 100
projects.active$log_people_pr = log(projects.active$people_pr)
projects.active$has_template = projects.active$issue_template | projects.active$pr_template
projects.active$has_url = projects.active$url
projects.active$external_commits = projects.active$year_commits - projects.active$core_commits
projects.active$external_commit_ratio = projects.active$external_commits / projects.active$year_commits
projects.active$had_external_committers = projects.active$external_commit_ratio > 0
summary(projects.active$num_labels)
projects.active$has_labels = projects.active$num_labels >= 5
nrow(projects.active)
summary(projects.active$pol_50)
projects.active$is_impolite = projects.active$pol_50 < as.numeric(quantile(projects.active$pol_50, na.rm=TRUE)[2]) 
projects.active$is_polite = projects.active$pol_50 > as.numeric(quantile(projects.active$pol_50, na.rm=TRUE)[4])
summary(projects.active$resp_50)
projects.active$is_fast = projects.active$resp_50 < as.numeric(quantile(projects.active$resp_50, na.rm=TRUE)[2]) 
projects.active$is_slow = projects.active$resp_50 > as.numeric(quantile(projects.active$resp_50, na.rm=TRUE)[4]) 
summary(projects.active$stars)

projects.active$not_slow = projects.active$resp_50 < as.numeric(quantile(projects.active$resp_50, na.rm=TRUE)[4]) 
projects.active$resp_days = projects.active$resp_50 / 24.0
summary(projects.active$resp_days)
projects.active$is_days_fast = projects.active$resp_days < as.numeric(quantile(projects.active$resp_days, na.rm=TRUE)[2]) 
projects.active$is_days_slow = projects.active$resp_days > as.numeric(quantile(projects.active$resp_days, na.rm=TRUE)[4]) 
projects.active$log_stars = log(projects.active$stars+1)
projects.active$log_age = log(projects.active$age)
projects.active$log_recent_commits = log(projects.active$recent_commits)
projects.active$log_num_headers = log(projects.active$num_headers_3)
projects.active$year_external_contributors = log(projects.active$year_contributors - projects.active$year_main_contributors + 1)

table(projects.active$readme_bytes == 0)
table(projects.active$issues > 10000)
table(projects.active$num_headers_3 == 0)
table(projects.active$num_headers_3 > 100)
table(projects.active$pol_50 == 0)
table(is.na(projects.active$pol_50))
table(projects.active$num_labels > 500)
table(projects.active$resp_50 < 1)
table(projects.active$recent_commits > 4000)
table(projects.active$lines_changed > 2000)
table(is.na(projects.active$lines_changed))
table(projects.active$year_main_contributors == 0)
table(projects.active$newcomers_delta < 0)
summary(projects.active$year_external_contributors)

ds = subset(projects.active,
            num_headers_3 > 0
            & readme_bytes > 0
            & pol_50 > 0
            & !is.na(pol_50)
            & resp_50 >= 1
            & !is.na(resp_50)
            & !is.na(lines_changed)
            & year_main_contributors > 0
            & recent_authors <= 90
            & newcomers_delta >= 0)

nrow(projects.active)
nrow(ds)

print_tex("tbl_data.tex", 
          stargazer(ds, 
                    omit.summary.stat="n",
                    median=TRUE,
                    align=TRUE,
                    digits=2,
                    column.sep.width="0pt"))

table(ds$has_newnew_contributors)

m_new = glm(has_newnew_contributors ~
              had_external_committers
            + log_age
            + log(issues + 1)
            + has_url
            + log_num_headers
            + has_contact
            + has_contrib
            + has_badges
            + has_labels
            + has_template
            + log_recent_commits
            + is_fast
            + log_stars
            + is_impolite
            + log_recent_commits * has_contrib
            + log_recent_commits * has_badges
            + log_recent_commits * has_url
         , family = "binomial"
         , data = ds)

summary(m_new)

vif(m_new) # done without interaction terms
pR2(m_new)
Anova(m_new)

interplot(m_new, "has_badgesTRUE", "log_recent_commits") +
  xlab("Num recent commits (log)") +
  ylab("Estimated coefficient for\nHas badges") +
  theme_bw() +
  geom_hline(yintercept = 0, linetype = "dashed")

interplot(m_new, "has_urlTRUE", "log_recent_commits")
interplot(m_new, "has_contribTRUE", "log_recent_commits")

m_all = glm(has_new_contributors ~
            had_external_committers
            + log_age
            + log(issues + 1)
            + has_url
            + log_num_headers
            + has_contact
            + has_contrib
            + has_badges
            + has_labels
            + has_template
            + log_recent_commits
            + is_fast
            + log_stars
            + is_impolite
            #+ log_recent_commits * has_contrib
            #+ log_recent_commits * has_badges
            #+ log_recent_commits * has_url
         , family = "binomial"
         , data = ds)
summary(m_all)
Anova(m_all)
vif(m_all) # done without interaction terms
interplot(m_all, "has_badgesTRUE", "log_recent_commits")

interplot(m_all, "has_urlTRUE", "log_recent_commits") +
  xlab("Num recent commits (log)") +
  ylab("Estimated coefficient for\nHas website") +
  theme_bw() +
  geom_hline(yintercept = 0, linetype = "dashed")

interplot(m_all, "has_contribTRUE", "log_recent_commits") +
  xlab("Num recent commits (log)") +
  ylab("Estimated coefficient for\nHas contrib") +
  # Change the background
  theme_bw() +
  geom_hline(yintercept = 0, linetype = "dashed")

v = as.data.frame(vif(m_all))
v$new = as.data.frame(vif(m_new))[,1]
names(v) = c("all", "new")
names(v)
v
xtable(v)

mcor <- round(cor(ds[,c("had_external_committers", "log_age", "issues",
                "has_url", "log_num_headers", "has_contact",
                "has_contrib", "has_badges", "has_labels",
                "has_template", "log_recent_commits", "is_fast",
                "log_stars", "is_impolite")]), 2)
upper <- mcor 
upper[upper.tri(mcor)] <- ""
upper <- as.data.frame(upper)
xtable(upper)

stargazer(m_all, m_new, title="Signals that help bring in new contributors", font.size="small", single.row=TRUE)


file="tex_model_all.csv"
modelNames=c("has new contributors", "has first-time GitHub contributors")
caption="Signals that help bring in new contributors"

mList = list(m1=m_all, m2=m_new)
makeTexRegCox(mList, file, modelNames, caption, digits=2)

print_Anova_glm(m_all, "anova_model_1.csv")
print_Anova_glm(m_new, "anova_model_2.csv")

