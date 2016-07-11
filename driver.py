import sys

from ReportWriter import ReportWriter
from CampaignDataSet import CampaignDataSet

mainDataFile = "data/source1.csv"
mediaTypeDataFile = "data/source2.csv"
reportFile = "source1_source2_report.csv"

if len(sys.argv) == 3:
	print "Running using\n   -Main data file: " + sys.argv[1] + "\n   -Media type file: " + sys.argv[2] + "   -Output report file: " + sys.argv[3] + "\n"
	mainDataFile = sys.argv[1]
	mediaTypeDataFile = sys.argv[2]
else:
	print "Command line arguments not found or invalid, defaulting to\n   -Main data file: " + mainDataFile + "\n   -Media type file: " + mediaTypeDataFile + "\n   -Output report file: " + reportFile + "\n"


myReport = ReportWriter(reportFile, CampaignDataSet(mainDataFile, mediaTypeDataFile))
print "\nUnique campaigns which occured in February: " + str(myReport.dataSet.uniqueCampaignsInMonth(2)) + "\n"
print "Total conversions on plant initiatives: " + str(myReport.dataSet.countActionsOnInitiative("plants","conversions")) + "\n"
print "The audience|asset combination with the least expensive average cost is: " + str(myReport.dataSet.leastExpensiveConversionAudienceByAsset())
print "*Assuming \"least expensive\" refers to the average value of (CPM || CPV)/(total conversions for this campaign instance) for each combination*\n"

print "The average cost per video was view: " + str(myReport.dataSet.averageCostPerVideoView())

print "Writing report..."
myReport.writeReport()

print "Done!  Report written to: " + reportFile